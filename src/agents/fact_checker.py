import os

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from src.agents.llm_factory import build_chat_llm

class FactCheckResult(BaseModel):
    is_accurate: bool = Field(
        description="True if the current simplified text is accurate according to the original complex text and preserves all core information. False if there are hallucinations or omissions."
    )
    feedback: str = Field(
        description="Specific instructions for the Simplifier Agent on what facts to correct or what core information is missing. Empty string if accurate."
    )

def node_fact_checker(state: dict) -> dict:
    
    llm = build_chat_llm(temperature=0.0, model=os.getenv("FACT_CHECKER_MODEL") or None, provider=os.getenv("FACT_CHECKER_PROVIDER") or None)
    
    fact_checker_agent = llm.with_structured_output(FactCheckResult)

    system_prompt = """You are a Medical Fact-Checker for PLAIN LANGUAGE SUMMARIES (PLS).
    
    Compare the Current Simplified Text against the Original Text.

    Do NOT penalize the draft for translating academic terms into everyday language. For example, translating "no statistically significant difference" to "didn't make a difference" or "was no better than" is EXACTLY what we want. This is NOT a distortion.
    Do NOT demand the inclusion of trial design terms (e.g., "allocation concealment", "blinding", "monopreparations", "risk of bias"). Patients do not need this.

    Look for:
    1. Omissions: Did the draft leave out any crucial data from the Core Information?
    2. Hallucinations: Did the draft invent data or facts not present in the original text?
    3. Distortion: Are the results or statistical findings exaggerated or minimized?

    If the medical truth is preserved in simple words, APPROVE IT. Only reject if they hallucinate a completely fake benefit or omit a deadly side effect. If you decide to reject it provide actionable feedback."""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Original Text:\n{complex_text}\n\nCurrent Simplified Text:\n{current_simplified_text}")
    ])
    
    chain = prompt | fact_checker_agent
    
    result = chain.invoke({
        "complex_text": state["complex_text"],
        "current_simplified_text": state["current_simplified_text"]
    })
    
    feedback_to_append = []
    if not result.is_accurate:
        feedback_to_append.append(f"[FACT-CHECKER FEEDBACK]: {result.feedback}")
    
    return {
        "is_fact_approved": result.is_accurate, 
        "feedback_history": feedback_to_append
    }