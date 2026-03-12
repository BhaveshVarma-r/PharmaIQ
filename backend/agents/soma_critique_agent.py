from backend.agents.base_critique import BaseCritiqueAgent


class SOMACritiqueAgent(BaseCritiqueAgent):
    def __init__(self, llm):
        super().__init__(
            agent_name="soma_critique",
            target_agent="SOMA",
            llm=llm
        )

    def critique_cold_chain_decision(
        self, soma_decision, original_sensor_data, revision_count=0
    ):
        from backend.rag.knowledge_base import get_cold_chain_context
        drug_names = " ".join([
            d.get("drug_name", "")
            for d in soma_decision.get("drugs_at_risk", [])
        ])
        rag_regulatory = get_cold_chain_context(
            "temperature breach classification WHO CDSCO {}".format(drug_names), n=3
        )
        drug_reference = {
            "vaccines": "2 to 8 degrees always, any above 8 degrees is CRITICAL",
            "insulin": "2 to 8 degrees unopened below 30 degrees in-use max 28 days NEVER FREEZE",
            "biologics": "2 to 8 degrees freeze-thaw is CRITICAL regardless of duration",
        }
        prompt_vars = {
            "soma_decision": str(soma_decision),
            "original_sensor_data": str(original_sensor_data),
            "drug_reference_data": str(drug_reference),
            "rag_regulatory_context": rag_regulatory,
        }
        return self.critique(
            decision=soma_decision,
            context={"sensor_data": original_sensor_data},
            prompt_name="cold_chain_critique",
            prompt_variables=prompt_vars,
            revision_count=revision_count,
        )

    def critique_staffing_decision(
        self, soma_decision, original_schedule_data, store_context, revision_count=0
    ):
        from backend.rag.knowledge_base import (
            get_regulatory_context, get_scheduling_context
        )
        rag_regulatory = get_regulatory_context(
            "Schedule H pharmacist dispensing requirements", n=2
        )
        rag_scheduling = get_scheduling_context(
            "pharmacy staffing compliance gaps", n=2
        )
        prompt_vars = {
            "soma_decision": str(soma_decision),
            "original_schedule_data": str(original_schedule_data),
            "store_context": str(store_context),
            "rag_regulatory_context": "{}\n\n{}".format(
                rag_regulatory, rag_scheduling
            ),
        }
        return self.critique(
            decision=soma_decision,
            context={
                "schedule_data": original_schedule_data,
                "store": store_context
            },
            prompt_name="staff_critique",
            prompt_variables=prompt_vars,
            revision_count=revision_count,
        )