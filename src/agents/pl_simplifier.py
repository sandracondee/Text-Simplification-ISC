import os
from concurrent.futures import ThreadPoolExecutor
from typing import Dict
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from src.agents.llm_factory import build_chat_llm

class SimplificationResult(BaseModel):
    current_simplified_text: str = Field(
        description="The resulting plain language summary, ensuring it is accessible to the widest possible audience "
        "(e.g., avoiding local idioms, using universally understood terms, and maintaining clear structures)."
    )

def _generate_single_draft(complex_text: str, model_name: str) -> str:
    llm = build_chat_llm(temperature=0.4, model=model_name)
    simplifier_agent = llm.with_structured_output(SimplificationResult)

    system_prompt = """You are a medical plain-language writer.
    Rewrite the biomedical abstract for the general public.

    Plain Language rules:
    - Keep every numerical and clinical fact faithful to the original.
    - Prefer short sentences and active voice.
    - Explain or rephrase jargon when needed.
    - Avoid academic bureaucracy and heavy statistical wording.
    - Do not add new claims, recommendations, or certainty not present in the source.
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Original biomedical abstract:\n{complex_text}\n\nWrite one plain-language version.")
    ])

    chain = prompt | simplifier_agent
    result = chain.invoke({"complex_text": complex_text})
    return result.current_simplified_text


def _resolve_provider() -> str:
    provider = os.getenv("LLM_PROVIDER", "").strip().lower()
    if provider:
        return provider
    local_mode = os.getenv("LOCAL_MODE", "").strip().lower() in {"1", "true", "yes", "on"}
    return "ollama" if local_mode else "gemini"


def _default_drafter_models() -> dict:
    provider = _resolve_provider()
    if provider == "ollama":
        base = os.getenv("OLLAMA_MODEL", "mistral")
        return {"A": base, "B": base, "C": base, "D": base}

    return {
        "A": "gemini-2.5-flash-lite",
        "B": "gemini-2.5-flash",
        "C": "gemini-2.0-flash",
        "D": "gemini-1.5-pro",
    }


def node_parallel_drafters(state: dict) -> dict:
    print("=" * 40)
    print(" PARALLEL DRAFTERS ")
    print("=" * 40)

    complex_text = state["complex_text"]

    defaults = _default_drafter_models()
    draft_models = {
        "A": os.getenv("DRAFTER_MODEL_A", defaults["A"]),
        "B": os.getenv("DRAFTER_MODEL_B", defaults["B"]),
        "C": os.getenv("DRAFTER_MODEL_C", defaults["C"]),
        "D": os.getenv("DRAFTER_MODEL_D", defaults["D"]),
    }

    drafts: Dict[str, str] = {}

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            letter: executor.submit(_generate_single_draft, complex_text, model_name)
            for letter, model_name in draft_models.items()
        }

        for letter, future in futures.items():
            try:
                drafts[letter] = future.result().strip()
            except Exception as exc:
                drafts[letter] = (
                    f"Draft generation failed for {letter}. "
                    f"Model '{draft_models[letter]}' error: {exc}"
                )

    return {"drafts": drafts}