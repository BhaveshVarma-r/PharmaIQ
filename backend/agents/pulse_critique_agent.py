from backend.agents.base_critique import BaseCritiqueAgent


class PULSECritiqueAgent(BaseCritiqueAgent):
    def __init__(self, llm):
        super().__init__(
            agent_name="pulse_critique",
            target_agent="PULSE",
            llm=llm
        )

    def critique_epidemic_forecast(
        self, pulse_decision, original_disease_data, inventory_data, revision_count=0
    ):
        from backend.rag.knowledge_base import get_disease_context
        disease = original_disease_data.get("disease_name", "unknown disease")
        rag_idsp = get_disease_context(
            "{} demand multiplier IDSP reporting lag".format(disease), n=2
        )
        drug_disease_reference = {
            "dengue": {
                "primary_sku": "Paracetamol 650mg NOT 500mg",
                "multiplier_range": "3 to 5x",
                "reporting_lag": "7 to 10 days"
            },
            "cholera": {
                "primary_sku": "ORS Sachets",
                "multiplier_range": "4 to 8x",
                "reporting_lag": "3 to 5 days"
            },
            "influenza": {
                "primary_sku": "Oseltamivir 75mg",
                "multiplier_range": "2 to 3.5x",
                "reporting_lag": "3 to 5 days"
            },
        }
        prompt_vars = {
            "pulse_decision": str(pulse_decision),
            "original_disease_data": str(original_disease_data),
            "inventory_data": str(inventory_data),
            "rag_idsp_context": rag_idsp,
            "drug_disease_reference": str(drug_disease_reference),
        }
        return self.critique(
            decision=pulse_decision,
            context={"disease_data": original_disease_data},
            prompt_name="forecast_critique",
            prompt_variables=prompt_vars,
            revision_count=revision_count,
        )

    def critique_demand_adjustment(
        self, pulse_decision, near_expiry_data, revision_count=0
    ):
        from backend.rag.knowledge_base import get_expiry_context
        rag_expiry = get_expiry_context(
            "near expiry markdown transfer return clearance", n=2
        )
        prompt_vars = {
            "pulse_decision": str(pulse_decision),
            "original_disease_data": str(near_expiry_data),
            "inventory_data": str(near_expiry_data),
            "rag_idsp_context": rag_expiry,
            "drug_disease_reference": "Near-expiry thresholds: Tier1 30 days Tier2 45 days Tier3 60 days",
        }
        return self.critique(
            decision=pulse_decision,
            context={"near_expiry_data": near_expiry_data},
            prompt_name="forecast_critique",
            prompt_variables=prompt_vars,
            revision_count=revision_count,
        )