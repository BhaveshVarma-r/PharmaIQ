import os
import json
import uuid
import logging
from typing import TypedDict, Optional, List, Dict, Any
from datetime import datetime

from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI

from backend.agents.soma_agent import SOMAAgent
from backend.agents.soma_critique_agent import SOMACritiqueAgent
from backend.agents.pulse_agent import PULSEAgent
from backend.agents.pulse_critique_agent import PULSECritiqueAgent
from backend.agents.planner_agent import PlannerAgent
from backend.agents.planner_critique_agent import PlannerCritiqueAgent

logger = logging.getLogger(__name__)


class PharmaIQState(TypedDict):
    event: Dict[str, Any]
    event_type: str
    store_id: Optional[str]
    fridge_id: Optional[str]
    planner_decomposition: Optional[Dict[str, Any]]
    planner_synthesis: Optional[Dict[str, Any]]
    planner_critique: Optional[Dict[str, Any]]
    planner_revision_count: int
    soma_decision: Optional[Dict[str, Any]]
    soma_critique: Optional[Dict[str, Any]]
    soma_revision_count: int
    soma_revision_instructions: Optional[str]
    pulse_decision: Optional[Dict[str, Any]]
    pulse_critique: Optional[Dict[str, Any]]
    pulse_revision_count: int
    pulse_revision_instructions: Optional[str]
    final_response: Optional[Dict[str, Any]]
    errors: List[str]
    trace: List[Dict[str, Any]]


def make_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.1,
    )


def planner_decompose_node(state: PharmaIQState) -> PharmaIQState:
    logger.info(
        "PLANNER: Decomposing event type={}".format(state["event_type"])
    )
    planner = PlannerAgent(make_llm())
    try:
        decomposition = planner.decompose_event(state["event"])
        state["planner_decomposition"] = decomposition
        state["trace"].append({
            "step": "planner_decompose",
            "timestamp": datetime.now().isoformat(),
            "result": decomposition.get("event_classification", {})
        })
    except Exception as e:
        logger.error("Planner decompose error: {}".format(e))
        state["errors"].append("planner_decompose: {}".format(e))
        state["planner_decomposition"] = {
            "event_classification": {
                "primary_domain": state["event_type"]
            },
            "task_sequence": []
        }
    return state


def soma_node(state: PharmaIQState) -> PharmaIQState:
    logger.info(
        "SOMA: Analysing event type={}".format(state["event_type"])
    )
    soma = SOMAAgent(make_llm())
    event = state["event"]
    store_id = state.get("store_id") or event.get("store_id", "MC0001")
    try:
        if state["event_type"] == "cold_chain_breach":
            fridge_id = state.get("fridge_id") or event.get(
                "fridge_id", "{}_FRIDGE_01".format(store_id)
            )
            sensor_data = event.get("sensor_data", {})
            decision = soma.analyse_cold_chain(
                store_id=store_id,
                fridge_id=fridge_id,
                sensor_data=sensor_data,
                revision_instructions=state.get("soma_revision_instructions")
            )
        else:
            disease_ctx = None
            if state.get("pulse_decision"):
                disease_ctx = (
                    "Active epidemic alert: {}. Footfall multiplier: {}".format(
                        state["pulse_decision"].get("disease_name", "Unknown"),
                        state["pulse_decision"].get(
                            "footfall_multiplier_for_soma", 1.3
                        )
                    )
                )
            decision = soma.analyse_staffing(
                store_id=store_id,
                disease_context=disease_ctx,
                revision_instructions=state.get("soma_revision_instructions")
            )
        state["soma_decision"] = decision
        state["trace"].append({
            "step": "soma_analysis",
            "timestamp": datetime.now().isoformat(),
            "decision_type": decision.get("decision_type"),
            "confidence": decision.get("confidence"),
        })
    except Exception as e:
        logger.error("SOMA node error: {}".format(e))
        state["errors"].append("soma_node: {}".format(e))
        state["soma_decision"] = {
            "error": str(e),
            "decision_type": "error"
        }
    return state


def soma_critique_node(state: PharmaIQState) -> PharmaIQState:
    logger.info("SOMA-CRITIQUE: Reviewing SOMA decision")
    soma_critique = SOMACritiqueAgent(make_llm())
    soma_decision = state.get("soma_decision", {})
    event = state["event"]
    try:
        if state["event_type"] == "cold_chain_breach":
            critique = soma_critique.critique_cold_chain_decision(
                soma_decision=soma_decision,
                original_sensor_data=event.get("sensor_data", {}),
                revision_count=state.get("soma_revision_count", 0)
            )
        else:
            critique = soma_critique.critique_staffing_decision(
                soma_decision=soma_decision,
                original_schedule_data=event.get("schedule_data", {}),
                store_context={"store_id": state.get("store_id")},
                revision_count=state.get("soma_revision_count", 0)
            )
        state["soma_critique"] = critique
        state["trace"].append({
            "step": "soma_critique",
            "timestamp": datetime.now().isoformat(),
            "verdict": critique.get("verdict"),
            "score": critique.get("overall_critique_score"),
        })
    except Exception as e:
        logger.error("SOMA critique error: {}".format(e))
        state["errors"].append("soma_critique: {}".format(e))
        state["soma_critique"] = {
            "verdict": "APPROVED",
            "error": str(e)
        }
    return state


def pulse_node(state: PharmaIQState) -> PharmaIQState:
    logger.info(
        "PULSE: Analysing event type={}".format(state["event_type"])
    )
    pulse = PULSEAgent(make_llm())
    event = state["event"]
    try:
        if state["event_type"] == "epidemic_alert":
            disease_alert = event.get("disease_alert", event)
            decision = pulse.generate_epidemic_forecast(
                disease_alert=disease_alert,
                revision_instructions=state.get("pulse_revision_instructions")
            )
        else:
            decision = pulse.analyse_near_expiry(
                days_threshold=60,
                store_id=state.get("store_id"),
                revision_instructions=state.get("pulse_revision_instructions")
            )
        state["pulse_decision"] = decision
        state["trace"].append({
            "step": "pulse_analysis",
            "timestamp": datetime.now().isoformat(),
            "decision_type": decision.get("decision_type"),
            "confidence": decision.get("confidence"),
        })
    except Exception as e:
        logger.error("PULSE node error: {}".format(e))
        state["errors"].append("pulse_node: {}".format(e))
        state["pulse_decision"] = {
            "error": str(e),
            "decision_type": "error"
        }
    return state


def pulse_critique_node(state: PharmaIQState) -> PharmaIQState:
    logger.info("PULSE-CRITIQUE: Reviewing PULSE decision")
    pulse_critique_agent = PULSECritiqueAgent(make_llm())
    pulse_decision = state.get("pulse_decision", {})
    event = state["event"]
    try:
        if pulse_decision.get("decision_type") == "epidemic_forecast":
            critique = pulse_critique_agent.critique_epidemic_forecast(
                pulse_decision=pulse_decision,
                original_disease_data=event.get("disease_alert", event),
                inventory_data={},
                revision_count=state.get("pulse_revision_count", 0)
            )
        else:
            critique = pulse_critique_agent.critique_demand_adjustment(
                pulse_decision=pulse_decision,
                near_expiry_data={},
                revision_count=state.get("pulse_revision_count", 0)
            )
        state["pulse_critique"] = critique
        state["trace"].append({
            "step": "pulse_critique",
            "timestamp": datetime.now().isoformat(),
            "verdict": critique.get("verdict"),
            "score": critique.get("overall_critique_score"),
        })
    except Exception as e:
        logger.error("PULSE critique error: {}".format(e))
        state["errors"].append("pulse_critique: {}".format(e))
        state["pulse_critique"] = {
            "verdict": "APPROVED",
            "error": str(e)
        }
    return state


def planner_synthesise_node(state: PharmaIQState) -> PharmaIQState:
    logger.info("PLANNER: Synthesising cross-domain decision")
    planner = PlannerAgent(make_llm())
    try:
        synthesis = planner.synthesise_cross_domain(
            original_event=state["event"],
            soma_decision=state.get("soma_decision", {}),
            soma_critique=state.get("soma_critique", {}),
            pulse_decision=state.get("pulse_decision", {}),
            pulse_critique=state.get("pulse_critique", {}),
        )
        state["planner_synthesis"] = synthesis
        state["trace"].append({
            "step": "planner_synthesis",
            "timestamp": datetime.now().isoformat(),
            "synthesis_status": synthesis.get("synthesis_status"),
            "action_count": len(
                synthesis.get("integrated_action_plan", [])
            ),
        })
    except Exception as e:
        logger.error("Planner synthesis error: {}".format(e))
        state["errors"].append("planner_synthesis: {}".format(e))
        state["planner_synthesis"] = {
            "synthesis_status": "ERROR",
            "error": str(e)
        }
    return state


def planner_critique_node(state: PharmaIQState) -> PharmaIQState:
    logger.info("PLANNER-CRITIQUE: Reviewing synthesis")
    planner_critique = PlannerCritiqueAgent(make_llm())
    try:
        critique = planner_critique.critique_plan(
            planner_decision=state.get("planner_synthesis", {}),
            original_event=state["event"],
            soma_decision=state.get("soma_decision", {}),
            soma_critique_verdict=state.get(
                "soma_critique", {}
            ).get("verdict", "UNKNOWN"),
            pulse_decision=state.get("pulse_decision", {}),
            pulse_critique_verdict=state.get(
                "pulse_critique", {}
            ).get("verdict", "UNKNOWN"),
            revision_count=state.get("planner_revision_count", 0)
        )
        state["planner_critique"] = critique
        state["trace"].append({
            "step": "planner_critique",
            "timestamp": datetime.now().isoformat(),
            "verdict": critique.get("verdict"),
            "score": critique.get("overall_critique_score"),
        })
    except Exception as e:
        logger.error("Planner critique error: {}".format(e))
        state["errors"].append("planner_critique: {}".format(e))
        state["planner_critique"] = {
            "verdict": "APPROVED",
            "error": str(e)
        }
    return state


def finalise_node(state: PharmaIQState) -> PharmaIQState:
    state["final_response"] = {
        "event_id": state["event"].get("event_id", str(uuid.uuid4())),
        "event_type": state["event_type"],
        "processed_at": datetime.now().isoformat(),
        "soma_decision": state.get("soma_decision"),
        "soma_critique_verdict": state.get(
            "soma_critique", {}
        ).get("verdict"),
        "pulse_decision": state.get("pulse_decision"),
        "pulse_critique_verdict": state.get(
            "pulse_critique", {}
        ).get("verdict"),
        "planner_synthesis": state.get("planner_synthesis"),
        "planner_critique_verdict": state.get(
            "planner_critique", {}
        ).get("verdict"),
        "integrated_action_plan": state.get(
            "planner_synthesis", {}
        ).get("integrated_action_plan", []),
        "store_communication": state.get(
            "planner_synthesis", {}
        ).get("store_operations_communication"),
        "total_financial_impact": state.get(
            "planner_synthesis", {}
        ).get("total_financial_impact_inr"),
        "trace": state["trace"],
        "errors": state["errors"],
    }
    logger.info(
        "PharmaIQ: Event processed. Actions: {}".format(
            len(state["final_response"]["integrated_action_plan"])
        )
    )
    return state


def route_after_soma_critique(state: PharmaIQState) -> str:
    critique = state.get("soma_critique", {})
    revision_count = state.get("soma_revision_count", 0)
    if critique.get("verdict") == "REJECTED" and revision_count < 2:
        issues = critique.get("specific_issues", [])
        instructions = "; ".join(
            [i.get("correction", "") for i in issues[:3]]
        )
        state["soma_revision_instructions"] = instructions
        state["soma_revision_count"] = revision_count + 1
        return "soma_revise"
    return "pulse"


def route_after_pulse_critique(state: PharmaIQState) -> str:
    critique = state.get("pulse_critique", {})
    revision_count = state.get("pulse_revision_count", 0)
    if critique.get("verdict") == "REJECTED" and revision_count < 2:
        issues = critique.get("specific_issues", [])
        instructions = "; ".join(
            [i.get("correction", "") for i in issues[:3]]
        )
        state["pulse_revision_instructions"] = instructions
        state["pulse_revision_count"] = revision_count + 1
        return "pulse_revise"
    return "planner_synthesise"


def route_after_planner_critique(state: PharmaIQState) -> str:
    critique = state.get("planner_critique", {})
    revision_count = state.get("planner_revision_count", 0)
    if critique.get("verdict") == "REJECTED" and revision_count < 1:
        state["planner_revision_count"] = revision_count + 1
        return "planner_revise"
    return "finalise"


def build_pharmaiq_graph():
    graph = StateGraph(PharmaIQState)

    graph.add_node("planner_decompose", planner_decompose_node)
    graph.add_node("soma", soma_node)
    graph.add_node("soma_critique", soma_critique_node)
    graph.add_node("pulse", pulse_node)
    graph.add_node("pulse_critique", pulse_critique_node)
    graph.add_node("planner_synthesise", planner_synthesise_node)
    graph.add_node("planner_critique", planner_critique_node)
    graph.add_node("finalise", finalise_node)

    graph.set_entry_point("planner_decompose")

    graph.add_edge("planner_decompose", "soma")
    graph.add_edge("soma", "soma_critique")

    graph.add_conditional_edges(
        "soma_critique",
        route_after_soma_critique,
        {
            "soma_revise": "soma",
            "pulse": "pulse"
        }
    )

    graph.add_edge("pulse", "pulse_critique")

    graph.add_conditional_edges(
        "pulse_critique",
        route_after_pulse_critique,
        {
            "pulse_revise": "pulse",
            "planner_synthesise": "planner_synthesise"
        }
    )

    graph.add_edge("planner_synthesise", "planner_critique")

    graph.add_conditional_edges(
        "planner_critique",
        route_after_planner_critique,
        {
            "planner_revise": "planner_synthesise",
            "finalise": "finalise"
        }
    )

    graph.add_edge("finalise", END)

    return graph.compile()


def run_pharmaiq(event: Dict[str, Any]) -> Dict[str, Any]:
    graph = build_pharmaiq_graph()
    initial_state: PharmaIQState = {
        "event": event,
        "event_type": event.get("event_type", "general"),
        "store_id": event.get("store_id"),
        "fridge_id": event.get("fridge_id"),
        "planner_decomposition": None,
        "planner_synthesis": None,
        "planner_critique": None,
        "planner_revision_count": 0,
        "soma_decision": None,
        "soma_critique": None,
        "soma_revision_count": 0,
        "soma_revision_instructions": None,
        "pulse_decision": None,
        "pulse_critique": None,
        "pulse_revision_count": 0,
        "pulse_revision_instructions": None,
        "final_response": None,
        "errors": [],
        "trace": [],
    }
    result = graph.invoke(initial_state)
    return result.get("final_response", {})