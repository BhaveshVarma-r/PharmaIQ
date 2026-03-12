import json
import uuid
import re
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class PlannerAgent:
    def __init__(self, llm):
        self.llm = llm
        self.agent_name = "PLANNER"

    def decompose_event(self, event, active_soma_tasks=None, active_pulse_tasks=None):
        from prompts.registry import registry
        from backend.rag.knowledge_base import get_cross_domain_context

        start_time = time.time()
        decision_id = str(uuid.uuid4())

        rag_context = get_cross_domain_context(
            "{} cross-domain cascade pattern".format(
                event.get("event_type", "pharmacy")
            ),
            n=2
        )

        prompt_vars = {
            "incoming_event": json.dumps(event, indent=2),
            "active_soma_tasks": json.dumps(active_soma_tasks or [], indent=2),
            "active_pulse_tasks": json.dumps(active_pulse_tasks or [], indent=2),
            "pending_approvals": "None",
            "system_alert_level": "NORMAL",
            "affected_store_context": json.dumps(
                event.get("affected_stores", []), indent=2
            ),
            "rag_pattern_context": rag_context,
        }

        system_prompt = registry.get_prompt("planner", "system")
        decomp_prompt = registry.get_prompt(
            "planner", "task_decomposition", prompt_vars
        )
        full_prompt = "{}\n\n{}".format(system_prompt, decomp_prompt)

        response = self._invoke_llm(full_prompt)
        decision = self._parse_response(response, "task_decomposition")
        decision["decision_id"] = decision_id
        decision["event_id"] = event.get("event_id", str(uuid.uuid4()))
        decision["latency_ms"] = int((time.time() - start_time) * 1000)

        self._persist_decision(decision)
        return decision

    def synthesise_cross_domain(
        self, original_event, soma_decision, soma_critique,
        pulse_decision, pulse_critique, revision_instructions=None
    ):
        from prompts.registry import registry
        from backend.rag.knowledge_base import get_cross_domain_context

        start_time = time.time()
        decision_id = str(uuid.uuid4())

        rag_context = get_cross_domain_context(
            "synthesis conflict resolution patient safety priority", n=2
        )

        authority_framework = {
            "autonomous": [
                "quarantine", "procurement_up_to_2.5x", "schedule_gap_alert"
            ],
            "store_manager": [
                "procurement_2.5x_to_3x", "schedule_h_suspension",
                "markdown_10_to_15pct"
            ],
            "head_of_ops": [
                "procurement_above_3x", "markdown_above_15pct",
                "10_plus_stores_affected"
            ],
            "cdsco": [
                "critical_cold_chain_patient_risk", "drug_recall",
                "schedule_h_violation_confirmed"
            ],
        }

        prompt_vars = {
            "soma_decision": json.dumps(soma_decision, indent=2),
            "pulse_decision": json.dumps(pulse_decision, indent=2),
            "soma_critique": json.dumps(soma_critique, indent=2),
            "pulse_critique": json.dumps(pulse_critique, indent=2),
            "original_event": json.dumps(original_event, indent=2),
            "operational_context": json.dumps({
                "timestamp": datetime.now().isoformat(),
                "soma_critique_verdict": soma_critique.get("verdict"),
                "pulse_critique_verdict": pulse_critique.get("verdict"),
            }, indent=2),
            "rag_pattern_context": rag_context,
            "authority_framework": json.dumps(authority_framework, indent=2),
        }

        if revision_instructions:
            prompt_vars["original_event"] += (
                "\n\nREVISION INSTRUCTIONS:\n{}".format(revision_instructions)
            )

        system_prompt = registry.get_prompt("planner", "system")
        synthesis_prompt = registry.get_prompt(
            "planner", "cross_domain_reasoning", prompt_vars
        )
        full_prompt = "{}\n\n{}".format(system_prompt, synthesis_prompt)

        response = self._invoke_llm(full_prompt)
        decision = self._parse_response(response, "cross_domain_synthesis")
        decision["decision_id"] = decision_id
        decision["latency_ms"] = int((time.time() - start_time) * 1000)

        self._persist_decision(decision)
        self._process_human_approvals(decision, original_event)
        return decision

    def _invoke_llm(self, prompt):
        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            logger.error("PLANNER LLM invocation failed: {}".format(e))
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
                "synthesis_status": "HUMAN_REQUIRED",
                "confidence": 0.3,
            }

    def _persist_decision(self, decision):
        from backend.database.sqlite_manager import insert_agent_decision
        insert_agent_decision({
            "decision_id": decision.get("decision_id", str(uuid.uuid4())),
            "agent_name": self.agent_name,
            "decision_type": decision.get("decision_type", "unknown"),
            "store_id": decision.get("store_id"),
            "details": decision,
            "confidence": decision.get("confidence"),
            "action_taken": json.dumps(
                decision.get("integrated_action_plan", [])[:3]
            ),
            "requires_human_approval": any(
                a.get("requires_human_approval")
                for a in decision.get("integrated_action_plan", [])
            ),
        })

    def _process_human_approvals(self, decision, event):
        from backend.database.sqlite_manager import add_to_human_approval_queue
        for action in decision.get("integrated_action_plan", []):
            if action.get("requires_human_approval"):
                add_to_human_approval_queue({
                    "decision_id": decision.get("decision_id"),
                    "agent_name": "PLANNER",
                    "action_description": action.get("action", "Unknown action"),
                    "full_context": {
                        "action": action,
                        "event": event,
                        "synthesis_status": decision.get("synthesis_status"),
                    },
                    "authority_required": action.get(
                        "approval_authority", "HEAD_OF_OPERATIONS"
                    ),
                    "store_id": action.get("store_id"),
                    "urgency": (
                        "CRITICAL"
                        if int(action.get("deadline_minutes", 999)) < 120
                        else "HIGH"
                    ),
                })