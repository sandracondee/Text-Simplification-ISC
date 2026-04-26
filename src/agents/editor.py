import os
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from src.agents.llm_factory import build_chat_llm


class EditorResult(BaseModel):
    current_simplified_text: str = Field(
        description="The corrected simplified text after applying the latest feedback only."
    )


def node_editor(state: dict) -> dict:
    print("=" * 40)
    print(" THE EDITOR ")
    print("=" * 40)

    llm = build_chat_llm(temperature=0.2, model=os.getenv("EDITOR_MODEL") or None)
    editor_agent = llm.with_structured_output(EditorResult)

    history = state.get("feedback_history", [])
    latest_feedback = "\n".join(history[-2:]) if history else "No feedback provided."

    system_prompt = """Correct the simplified text based SOLELY on this audit feedback.
Keep the rest of the text intact.
Do not introduce new claims and do not remove correct information that was not flagged.
Return only the corrected text."""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        (
            "human",
            "Current simplified text:\n{current_simplified_text}\n\n"
            "Latest audit feedback:\n{latest_feedback}",
        ),
    ])

    chain = prompt | editor_agent
    result = chain.invoke(
        {
            "current_simplified_text": state["current_simplified_text"],
            "latest_feedback": latest_feedback,
        }
    )

    return {
        "current_simplified_text": result.current_simplified_text,
        "iteration_count": state.get("iteration_count", 0) + 1,
    }