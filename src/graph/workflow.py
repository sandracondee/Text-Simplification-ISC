from langgraph.graph import END, StateGraph, START
from src.state import GraphState
from src.agents.pl_simplifier import node_parallel_drafters
from src.agents.judge import node_judge
from src.agents.fact_checker import node_fact_checker
from src.agents.readability_evaluator import node_readability_evaluator
from src.agents.editor import node_editor
from src.agents.glossary_builder import node_term_explainer

MAX_ITER = 3

def node_auditors(state: GraphState) -> dict:
    """
    Aggregates both auditor decisions into a single approval flag.
    """
    fact_ok = state.get("is_fact_approved", False)
    read_ok = state.get("is_readability_approved", False)

    return {
        "is_approved": fact_ok and read_ok
    }

def router_logic(state: GraphState) -> str:
    """
    Decides the next step after the parallel auditing phase.
    """
    fact_ok = state.get("is_fact_approved", False)
    readability_ok = state.get("is_readability_approved", False)
    approved = fact_ok and readability_ok

    print(
        f"\n--- ROUTER: Iteration {state.get('iteration_count', 0)}, "
        f"Fact: {fact_ok}, Readability: {readability_ok} ---"
    )

    if approved:
        print("-> AUDIT APPROVED. Workflow finished.")
        return "term_explainer"

    if state["iteration_count"] >= MAX_ITER:
        print(f"-> MAX ITERATIONS REACHED ({MAX_ITER}). Workflow finished.")
        return END

    print("-> AUDIT REJECTED. Routing to editor for correction.")
    return "editor"

def build_graph():
    """
    Constructs and compiles the MoA State Graph using Draft-Select-Audit-Edit.
    """
    workflow = StateGraph(GraphState)

    workflow.add_node("parallel_drafters", node_parallel_drafters)
    workflow.add_node("judge", node_judge)
    workflow.add_node("fact_checker", node_fact_checker)
    workflow.add_node("readability_evaluator", node_readability_evaluator)
    workflow.add_node("auditors", node_auditors)
    workflow.add_node("editor", node_editor)
    workflow.add_node("term_explainer", node_term_explainer)

    workflow.add_edge(START, "parallel_drafters")
    workflow.add_edge("parallel_drafters", "judge")

    workflow.add_edge("judge", "fact_checker")
    workflow.add_edge("judge", "readability_evaluator")

    workflow.add_edge("editor", "fact_checker")
    workflow.add_edge("editor", "readability_evaluator")

    workflow.add_edge("fact_checker", "auditors")
    workflow.add_edge("readability_evaluator", "auditors")

    workflow.add_conditional_edges(
        "auditors",
        router_logic,
        {
            "editor": "editor",
            "term_explainer": "term_explainer",
        }
    )

    workflow.add_edge("term_explainer", END)

    return workflow.compile()