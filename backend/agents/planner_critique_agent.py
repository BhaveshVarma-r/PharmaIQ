from backend.agents.base_critique import BaseCritiqueAgent


class PlannerCritiqueAgent(BaseCritiqueAgent):
    def __init__(self, llm):
        super().__init__(
            agent_name="planner_critique",
            target_agent="PLANNER",
            llm=llm
        )

    def critique_plan(
        self, planner_decision, original_event, soma_decision,
        soma_critique_verdict, pulse_decision, pulse_critique_verdict,
        revision_count=0
    ):
        from backend.rag.knowledge_base import (
            get_cross_domain_context, get_regulatory_context
        )
        rag_patterns = get_cross_domain_context(
            "cross-domain cascade epidemic cold chain staffing cascade", n=3
        )
        rag_authority = get_regulatory_context(
            "human authority procurement approval Schedule H CDSCO", n=2
        )
        authority_framework = {
            "system_autonomous": [
                "batch_quarantine_any", "staff_gap_alert",
                "procurement_up_2.5x", "markdown_up_10pct"
            ],
            "store_manager_required": [
                "procurement_2.5x_3x", "schedule_h_suspension",
                "markdown_10_15pct"
            ],
            "head_of_ops_required": [
                "procurement_above_3x", "markdown_above_15pct",
                "10_plus_stores"
            ],
            "cdsco_notification_required": [
                "critical_cold_chain_patient_risk", "drug_recall",
                "schedule_h_confirmed"
            ],
        }
        prompt_vars = {
            "planner_decision": str(planner_decision),
            "original_event": str(original_event),
            "soma_decision": str(soma_decision),
            "soma_critique_verdict": soma_critique_verdict,
            "pulse_decision": str(pulse_decision),
            "pulse_critique_verdict": pulse_critique_verdict,
            "rag_pattern_context": "{}\n\n{}".format(rag_patterns, rag_authority),
            "authority_framework": str(authority_framework),
        }
        return self.critique(
            decision=planner_decision,
            context={
                "original_event": original_event,
                "soma_verdict": soma_critique_verdict,
                "pulse_verdict": pulse_critique_verdict,
            },
            prompt_name="plan_critique",
            prompt_variables=prompt_vars,
            revision_count=revision_count,
        )