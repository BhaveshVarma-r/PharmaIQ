import json
import uuid
import re
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class BaseCritiqueAgent:
    MAX_REVISIONS = 2

    def __init__(self, agent_name, target_agent, llm):
        self.agent_name = agent_name
        self.target_agent = target_agent
        self.llm = llm

    def critique(self, decision, context, prompt_name, prompt_variables, revision_count=0):
        start_time = time.time()
        from prompts.registry import registry
        system_prompt = registry.get_prompt(self.agent_name, "system")
        critique_prompt = registry.get_prompt(
            self.agent_name, prompt_name, prompt_variables
        )
        full_prompt = "{}\n\n{}".format(system_prompt, critique_prompt)
        try:
            response = self.llm.invoke(full_prompt)
            raw_content = response.content
            critique_result = self._parse_critique_response(raw_content)
        except Exception as e:
            logger.error("{} LLM error: {}".format(self.agent_name, e))
            critique_result = self._fallback_critique(str(e))

        critique_result["critique_agent"] = self.agent_name
        critique_result["target_agent"] = self.target_agent
        critique_result["target_decision_id"] = decision.get(
            "decision_id", str(uuid.uuid4())
        )
        critique_result["revision_count"] = revision_count
        critique_result["latency_ms"] = int((time.time() - start_time) * 1000)

        self._log_critique(critique_result)

        if critique_result.get("escalate_to_human"):
            self._escalate_to_human(critique_result, decision, context)

        return critique_result

    def _parse_critique_response(self, raw):
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
            logger.warning("{}: Failed to parse JSON response".format(self.agent_name))
            return {
                "verdict": "APPROVED_WITH_MODIFICATIONS",
                "overall_critique_score": 0.6,
                "dimension_scores": {},
                "specific_issues": [
                    {
                        "severity": "MINOR",
                        "issue": "Critique response parsing failed",
                        "correction": "Manual review recommended"
                    }
                ],
                "approved_elements": [],
                "required_modifications": [
                    "Manual review required - critique parsing failed"
                ],
                "critique_reasoning": "Raw response: {}".format(raw[:500]),
                "critique_confidence": 0.4,
                "escalate_to_human": True,
                "escalation_reason": "Critique agent response could not be parsed",
            }

    def _fallback_critique(self, error_msg):
        return {
            "verdict": "APPROVED_WITH_MODIFICATIONS",
            "overall_critique_score": 0.5,
            "dimension_scores": {},
            "specific_issues": [
                {
                    "severity": "SIGNIFICANT",
                    "issue": "Critique LLM error: {}".format(error_msg),
                    "correction": "Human review required"
                }
            ],
            "approved_elements": [],
            "required_modifications": [
                "LLM error - human review required before action"
            ],
            "critique_reasoning": "Critique agent encountered an error: {}".format(
                error_msg
            ),
            "critique_confidence": 0.3,
            "escalate_to_human": True,
            "escalation_reason": "Critique agent LLM error: {}".format(error_msg),
        }

    def _log_critique(self, critique):
        try:
            from backend.database.sqlite_manager import write_critique_log, write_audit_log
            write_critique_log(critique)
            write_audit_log({
                "event_type": "CRITIQUE_{}".format(self.agent_name),
                "agent_name": self.agent_name,
                "decision_id": critique.get("target_decision_id"),
                "action_description": (
                    "{} reviewed {} decision: VERDICT={} SCORE={}".format(
                        self.agent_name, self.target_agent,
                        critique.get("verdict"),
                        critique.get("overall_critique_score")
                    )
                ),
                "after_state": {
                    "verdict": critique.get("verdict"),
                    "score": critique.get("overall_critique_score"),
                    "issues_count": len(critique.get("specific_issues", [])),
                }
            })
        except Exception as e:
            logger.error("Failed to log critique: {}".format(e))

    def _escalate_to_human(self, critique, decision, context):
        try:
            from backend.database.sqlite_manager import add_to_human_approval_queue
            add_to_human_approval_queue({
                "decision_id": critique.get(
                    "target_decision_id", str(uuid.uuid4())
                ),
                "agent_name": self.agent_name,
                "action_description": "Critique escalation: {}".format(
                    critique.get("escalation_reason", "Manual review required")
                ),
                "full_context": {
                    "critique": critique,
                    "original_decision": decision,
                },
                "authority_required": "HEAD_OF_OPERATIONS",
                "store_id": decision.get("store_id"),
                "urgency": "HIGH",
            })
        except Exception as e:
            logger.error(
                "Failed to add critique escalation to queue: {}".format(e)
            )

    def should_request_revision(self, critique, revision_count):
        if critique.get("verdict") == "REJECTED" and revision_count < self.MAX_REVISIONS:
            return True
        blocking = [
            i for i in critique.get("specific_issues", [])
            if i.get("severity") == "BLOCKING"
        ]
        return len(blocking) > 0 and revision_count < self.MAX_REVISIONS