import re
import os
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from src.agents.llm_factory import build_chat_llm


class JudgeResult(BaseModel):
    rationale: str = Field(description="Short rationale for the selected draft.")
    winner: str = Field(description="Winning option letter: A, B, C, or D.")


def _normalize_winner(raw_winner: str) -> str:
    cleaned = (raw_winner or "").strip().upper()
    if cleaned in {"A", "B", "C", "D"}:
        return cleaned

    match = re.search(r"\b([ABCD])\b", cleaned)
    if match:
        return match.group(1)
    return "A"


def node_judge(state: dict) -> dict:
    print("=" * 40)
    print(" THE JUDGE ")
    print("=" * 40)

    llm = build_chat_llm(temperature=0.1, model=os.getenv("JUDGE_MODEL") or None)
    judge_agent = llm.with_structured_output(JudgeResult)

    drafts = state.get("drafts", {})

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """You are a Plain Language Style Judge.
Evaluate options A, B, C, and D against the original biomedical text.
Prioritize plain language quality, clarity, and structure.
Do NOT evaluate numerical accuracy.
You must provide a winner letter among A/B/C/D.
At the very end of your internal decision this format must be respected: WINNER: [Letter].""",
        ),
        (
            "human",
            "Original biomedical text:\n{complex_text}\n\n"
            "Option A:\n{draft_a}\n\n"
            "Option B:\n{draft_b}\n\n"
            "Option C:\n{draft_c}\n\n"
            "Option D:\n{draft_d}\n\n"
            "Select the winner and provide the winner letter.",
        ),
    ])

    chain = prompt | judge_agent
    result = chain.invoke(
        {
            "complex_text": state["complex_text"],
            "draft_a": drafts.get("A", ""),
            "draft_b": drafts.get("B", ""),
            "draft_c": drafts.get("C", ""),
            "draft_d": drafts.get("D", ""),
        }
    )

    winner = _normalize_winner(result.winner)
    selected_text = drafts.get(winner, drafts.get("A", ""))

    return {
        "selected_draft_letter": winner,
        "current_simplified_text": selected_text,
    }