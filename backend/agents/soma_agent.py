import json
import uuid
import re
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class SOMAAgent:
    def __init__(self, llm):
        self.llm = llm
        self.agent_name = "SOMA"

    def analyse_cold_chain(
        self, store_id, fridge_id, sensor_data, revision_instructions=None
    ):
        from prompts.registry import registry
        from backend.mcp_servers.cold_chain_mcp import ColdChainMCPServer
        from backend.rag.knowledge_base import get_cold_chain_context

        start_time = time.time()
        decision_id = str(uuid.uuid4())
        cold_chain_mcp = ColdChainMCPServer()

        history_result = cold_chain_mcp.get_fridge_history(fridge_id, hours=24)
        historical_context = history_result.get("data", {}).get("readings", [])[:10]

        store_fridges = cold_chain_mcp.get_store_fridges(store_id)
        store_fridge_context = store_fridges.get("data", {}).get("fridges", [])

        rag_context = get_cold_chain_context(
            "temperature breach {} {}".format(
                sensor_data.get("temperature"),
                sensor_data.get("breach_type", "")
            ),
            n=3
        )

        store_info = self._get_store_info(store_id)
        soma_version = registry.get_active_version("soma")

        prompt_vars = {
            "sensor_data": json.dumps(sensor_data, indent=2),
            "historical_context": json.dumps(historical_context, indent=2),
            "drugs_at_risk": json.dumps(
                sensor_data.get("drugs_at_risk", []), indent=2
            ),
            "rag_context": rag_context,
            "store_id": store_id,
            "store_name": store_info.get("store_name", "Unknown"),
            "city": store_info.get("city", "Unknown"),
            "local_time": datetime.now().strftime("%H:%M"),
            "store_status": "OPEN" if 8 <= datetime.now().hour < 22 else "CLOSED",
            "store_fridge_context": json.dumps(store_fridge_context, indent=2),
            "city_breach_context": "No city-wide breach pattern detected",
        }

        if revision_instructions:
            prompt_vars["sensor_data"] = (
                prompt_vars["sensor_data"] +
                "\n\nREVISION INSTRUCTIONS FROM CRITIQUE:\n{}".format(
                    revision_instructions
                )
            )

        system_prompt = registry.get_prompt("soma", "system")
        analysis_prompt = registry.get_prompt(
            "soma", "cold_chain_analysis", prompt_vars
        )
        full_prompt = "{}\n\n{}".format(system_prompt, analysis_prompt)

        response = self._invoke_llm(full_prompt)
        decision = self._parse_response(response, "cold_chain_analysis", store_id)
        decision["decision_id"] = decision_id
        decision["latency_ms"] = int((time.time() - start_time) * 1000)
        decision["prompt_version"] = soma_version

        self._persist_decision(decision)
        self._auto_quarantine(decision, store_id, fridge_id, cold_chain_mcp)

        return decision

    def analyse_staffing(
        self, store_id, target_date=None, disease_context=None,
        revision_instructions=None
    ):
        from prompts.registry import registry
        from backend.mcp_servers.hrms_mcp import HRMSMCPServer
        from backend.rag.knowledge_base import (
            get_scheduling_context, get_regulatory_context
        )

        start_time = time.time()
        decision_id = str(uuid.uuid4())
        hrms_mcp = HRMSMCPServer()

        schedule_result = hrms_mcp.get_weekly_schedule(store_id)
        schedule_data = schedule_result.get("data", {}).get("schedules", {})

        store_info = self._get_store_info(store_id)
        rag_context = get_scheduling_context(
            "pharmacy staffing Schedule H compliance {}".format(
                store_info.get("city", "")
            ),
            n=2
        )
        regulatory_context = get_regulatory_context(
            "Schedule H pharmacist requirements", n=2
        )

        month = datetime.now().month
        if 6 <= month <= 9:
            season = "monsoon"
            multiplier = 1.2
        elif month >= 11 or month <= 1:
            season = "winter"
            multiplier = 1.25
        else:
            season = "standard"
            multiplier = 1.0

        prompt_vars = {
            "schedule_data": json.dumps(schedule_data, indent=2),
            "store_id": store_id,
            "store_name": store_info.get("store_name", "Unknown"),
            "city": store_info.get("city", "Unknown"),
            "operating_hours": "08:00-22:00",
            "avg_daily_patients": str(store_info.get("avg_daily_patients", 150)),
            "footfall_forecast": "Based on 7-day rolling average",
            "disease_context": (
                disease_context or "No active disease alerts for this district"
            ),
            "staff_roster": json.dumps(
                list(schedule_data.values())[:3], indent=2
            ),
            "compliance_status": "Under review",
            "rag_context": "{}\n{}".format(rag_context, regulatory_context),
            "current_season": season,
            "seasonal_multiplier": str(multiplier),
            "season_rationale": "{} season apply {}x footfall multiplier".format(
                season.title(), multiplier
            ),
        }

        if revision_instructions:
            prompt_vars["schedule_data"] += (
                "\n\nREVISION INSTRUCTIONS:\n{}".format(revision_instructions)
            )

        system_prompt = registry.get_prompt("soma", "system")
        staff_prompt = registry.get_prompt("soma", "staff_scheduling", prompt_vars)
        full_prompt = "{}\n\n{}".format(system_prompt, staff_prompt)

        response = self._invoke_llm(full_prompt)
        decision = self._parse_response(response, "staff_scheduling", store_id)
        decision["decision_id"] = decision_id
        decision["latency_ms"] = int((time.time() - start_time) * 1000)

        self._persist_decision(decision)
        self._auto_flag_gaps(decision, store_id, hrms_mcp)

        return decision

    def _invoke_llm(self, prompt):
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            logger.error("SOMA LLM invocation failed: {}".format(e))
            raise

    def _parse_response(self, raw, decision_type, store_id):
        try:
            cleaned = raw.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                cleaned = "\n".join(lines[1:-1])
            result = json.loads(cleaned)
            result["store_id"] = store_id
            return result
        except json.JSONDecodeError:
            json_match = re.search(r'\{.*\}', raw, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    result["store_id"] = store_id
                    return result
                except Exception:
                    pass
            return {
                "decision_type": decision_type,
                "store_id": store_id,
                "raw_response": raw[:1000],
                "parse_error": True,
                "confidence": 0.3,
                "requires_human_approval": True,
            }

    def _get_store_info(self, store_id):
        from backend.database.sqlite_manager import get_store_by_id
        return get_store_by_id(store_id) or {}

    def _persist_decision(self, decision):
        from backend.database.sqlite_manager import insert_agent_decision
        insert_agent_decision({
            "decision_id": decision.get("decision_id", str(uuid.uuid4())),
            "agent_name": self.agent_name,
            "decision_type": decision.get("decision_type", "unknown"),
            "store_id": decision.get("store_id"),
            "details": decision,
            "confidence": decision.get("confidence"),
            "action_taken": json.dumps(decision.get("immediate_actions", [])),
            "requires_human_approval": decision.get(
                "requires_human_approval", False
            ),
        })

    def _auto_quarantine(self, decision, store_id, fridge_id, cold_chain_mcp):
        if decision.get("breach_classification") in ["MODERATE", "CRITICAL"]:
            for drug in decision.get("drugs_at_risk", []):
                if drug.get("action") == "QUARANTINE":
                    cold_chain_mcp.quarantine_batch(
                        store_id=store_id,
                        fridge_id=fridge_id,
                        batch_number=drug.get("batch_number", "UNKNOWN"),
                        drug_name=drug.get("drug_name", "UNKNOWN"),
                        reason="Cold chain breach: {}".format(
                            decision.get("breach_classification")
                        )
                    )

    def _auto_flag_gaps(self, decision, store_id, hrms_mcp):
        for gap in decision.get("compliance_gaps", []):
            if gap.get("severity") == "CRITICAL" and gap.get("schedule_h_risk"):
                hrms_mcp.flag_compliance_breach(
                    store_id=store_id,
                    date_str=gap.get("date", ""),
                    time_window=gap.get("time_window", ""),
                    gap_type=gap.get("gap_type", "NO_PHARMACIST")
                )