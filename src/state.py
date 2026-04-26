from typing import TypedDict, Annotated, List, Dict
import operator

class GraphState(TypedDict):
    complex_text: str
    reference_text: str
    drafts: Dict[str, str]
    selected_draft_letter: str
    current_simplified_text: str
    current_metrics: dict
    feedback_history: Annotated[List[str], operator.add]
    iteration_count: int
    is_fact_approved: bool
    is_readability_approved: bool
    is_approved: bool