from typing import TypedDict, Annotated, List
import operator

class GraphState(TypedDict):
    complex_text: str
    reference_text: str
    core_information: str
    current_simplified_text: str
    feedback_history: Annotated[List[str], operator.add]
    iteration_count: int
    is_approved: bool