import json
import uuid
import re
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class PULSEAgent:
    def __init__(self, llm):
        self.llm = llm
        self.agent_name = "PULSE"

    def generate_epidemic_forecast(self, disease_alert, revision_instructions=None):
        from prompts.registry import registry
        from backend.mcp_servers.erp_mcp import ERPMCPServer
        from backend.mcp_servers.disease_surveillance_mcp import (
            DiseaseSurveillanceMCPServer
        )
        from backend.mcp_servers.distributor_mcp import DistributorMCPServer
        from backend.rag.knowledge_base import get_disease_context

        start_time = time.time()
        decision_id = str(uuid.uuid4())

        erp_mcp = ERPMCPServer()
        surveillance_mcp = DiseaseSurveillanceMCPServer()
        distributor_mcp = DistributorMCPServer()

        city = disease_alert.get("city", "")
        disease = disease_alert.get("disease_name", "")
        district = disease_alert.get("district", "")

        affected_stores_result = surveillance_mcp.get_stores_in_alert_zone(
            disease_alert.get("alert_id", "")
        )
        affected_stores = affected_stores_result.get(
            "data", {}
        ).get("affected_stores", [])[:10]

        inventory_data = []
        if affected_stores:
            inv_result = erp_mcp.get_store_inventory(
                affected_stores[0]["store_id"]
            )
            inventory_data = inv_result.get("data", {}).get("inventory", [])[:15]

        rag_context = get_disease_context(
            "{} IDSP demand pattern forecast".format(disease), n=2
        )
        drug_disease_ref = surveillance_mcp.get_disease_sku_mapping(disease)
        drug_reference = drug_disease_ref.get("data", {})

        prompt_vars = {
            "disease_alert_data": json.dumps(disease_alert, indent=2),
            "affected_stores": json.dumps(affected_stores, indent=2),
            "current_inventory": json.dumps(inventory_data, indent=2),
            "historical_demand": "12-week rolling average simulated",
            "rag_epidemic_context": rag_context,
            "district": district,
            "city": city,
            "population_density": (
                "HIGH" if city in ["Delhi", "Mumbai"] else "MEDIUM"
            ),
            "monsoon_status": (
                "Active" if 6 <= datetime.now().month <= 9 else "Inactive"
            ),
            "hospital_context": "Major hospitals within 5km radius estimated",
        }

        if revision_instructions:
            prompt_vars["disease_alert_data"] += (
                "\n\nREVISION INSTRUCTIONS:\n{}".format(revision_instructions)
            )

        system_prompt = registry.get_prompt("pulse", "system")
        forecast_prompt = registry.get_prompt(
            "pulse", "epidemic_forecast", prompt_vars
        )
        full_prompt = "{}\n\n{}".format(system_prompt, forecast_prompt)

        response = self._invoke_llm(full_prompt)
        decision = self._parse_response(response, "epidemic_forecast")
        decision["decision_id"] = decision_id
        decision["latency_ms"] = int((time.time() - start_time) * 1000)

        self._persist_decision(decision)
        self._auto_execute_procurement(decision, distributor_mcp, disease)

        return decision

    def analyse_near_expiry(
        self, days_threshold=60, store_id=None, revision_instructions=None
    ):
        from prompts.registry import registry
        from backend.mcp_servers.erp_mcp import ERPMCPServer
        from backend.rag.knowledge_base import get_expiry_context

        start_time = time.time()
        decision_id = str(uuid.uuid4())
        erp_mcp = ERPMCPServer()

        expiry_result = erp_mcp.get_near_expiry_report(days_threshold)
        near_expiry_items = expiry_result.get("data", {}).get("items", [])

        if store_id:
            near_expiry_items = [
                i for i in near_expiry_items if i.get("store_id") == store_id
            ]

        rag_context = get_expiry_context(
            "near expiry clearance transfer markdown return", n=2
        )

        prompt_vars = {
            "near_expiry_inventory": json.dumps(near_expiry_items[:20], indent=2),
            "sales_velocity_data": "Average daily velocity from inventory records",
            "distance_matrix": "Inter-store distances within same city average 15km",
            "markdown_history": "Historical markdown success rate 72 percent for items above 45 days to expiry",
            "rag_clearance_context": rag_context,
        }

        if revision_instructions:
            prompt_vars["near_expiry_inventory"] += (
                "\n\nREVISION INSTRUCTIONS:\n{}".format(revision_instructions)
            )

        system_prompt = registry.get_prompt("pulse", "system")
        adjustment_prompt = registry.get_prompt(
            "pulse", "demand_adjustment", prompt_vars
        )
        full_prompt = "{}\n\n{}".format(system_prompt, adjustment_prompt)

        response = self._invoke_llm(full_prompt)
        decision = self._parse_response(response, "demand_adjustment")
        decision["decision_id"] = decision_id
        decision["latency_ms"] = int((time.time() - start_time) * 1000)

        self._persist_decision(decision)
        return decision

    def _invoke_llm(self, prompt):
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            logger.error("PULSE LLM invocation failed: {}".format(e))
            raise

    def _parse_response(self, raw, decision_type):
        try:
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                cleaned = "\n".join(lines[1:-1])
            return json.loads(cleaned)
        except json.JSONDecodeError:
            json_match = re.search(r'\{.*\}', raw, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except Exception:
                    pass
            return {
                "decision_type": decision_type,
                "raw_response": raw[:1000],
                "parse_error": True,
                "confidence": 0.3,
                "requires_human_approval": True,
            }

    def _persist_decision(self, decision):
        from backend.database.sqlite_manager import insert_agent_decision
        insert_agent_decision({
            "decision_id": decision.get("decision_id", str(uuid.uuid4())),
            "agent_name": self.agent_name,
            "decision_type": decision.get("decision_type", "unknown"),
            "store_id": None,
            "details": decision,
            "confidence": decision.get("confidence"),
            "action_taken": json.dumps(
                decision.get("recommended_actions", [])[:3]
            ),
            "requires_human_approval": decision.get(
                "requires_human_approval", False
            ),
        })

    def _auto_execute_procurement(self, decision, distributor_mcp, disease_name):
        for action in decision.get("recommended_actions", []):
            if (
                action.get("action_type") == "PROCUREMENT"
                and action.get("within_autonomous_authority")
                and float(action.get("procurement_multiplier", 3)) <= 2.5
            ):
                distributor_mcp.create_procurement_order(
                    store_id=action.get("store_id", "ALL"),
                    sku_id=action.get("sku_id", "UNKNOWN"),
                    drug_name=action.get("sku_id", "Unknown Drug"),
                    quantity=int(action.get("quantity", 0)),
                    order_type="epidemic_preemptive",
                    reason="Epidemic demand forecast: {}".format(disease_name),
                )