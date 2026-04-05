from langgraph.graph import END, StateGraph, START
from src.state import GraphState
from src.agents.analyst import node_analyst
from src.agents.pl_simplifier import node_pl_simplifier
from src.agents.fact_checker import node_fact_checker
from src.agents.readability_evaluator import node_readability_evaluator

MAX_ITER = 3

def node_final_approval(state: GraphState) -> dict:
    """
    Returns the final approval result: True if both evaluators approve the simplification, False otherwise.
    It also ensures the metrics report is passed to the final state.
    """
    fact_ok = state.get("is_fact_approved", False)
    read_ok = state.get("is_readability_approved", False)

    final_approval = fact_ok and read_ok

    return {
        "is_approved": final_approval
    }

def router_logic(state: GraphState) -> str:
    """
    Decides the next step after the evaluation phase.
    """
    print(f"\n--- ROUTER: Iteration {state['iteration_count']}, Approved: {state['is_approved']} ---")
    
    # Both evaluators approved the text
    if state["is_approved"]:
        print("-> SIMPLIFICATION APPROVED.")
        return END
    
    # Simplification rejected, but the max loops have been reached
    if state["iteration_count"] >= MAX_ITER:
        print(f"-> MAX ITERATIONS REACHED {MAX_ITER}. Simplification finished.")
        return END
        
    # Simplification rejected and there are attempts left
    print("-> SIMPLIFICATION REJECTED. Simplification will be improved.")
    return "simplifier"

def build_graph():
    """
    Constructs and compiles the Multi-Agent State Graph.
    """
    workflow = StateGraph(GraphState)

    workflow.add_node("analyst", node_analyst)
    workflow.add_node("simplifier", node_pl_simplifier)
    workflow.add_node("fact_checker", node_fact_checker)
    workflow.add_node("readability_evaluator", node_readability_evaluator)
    workflow.add_node("final_approval", node_final_approval)

    workflow.add_edge(START, "analyst")
    workflow.add_edge("analyst", "simplifier")
    
    workflow.add_edge("simplifier", "fact_checker")
    workflow.add_edge("simplifier", "readability_evaluator")

    workflow.add_edge("fact_checker", "final_approval")
    workflow.add_edge("readability_evaluator", "final_approval")

    workflow.add_conditional_edges(
        "final_approval",
        router_logic,
        {
            "simplifier": "simplifier",
            END: END
        }
    )

    return workflow.compile()