from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

class FactCheckResult(BaseModel):
    is_accurate: bool = Field(
        description="True if the current simplified text is accurate according to the original complex text and preserves all core information. False if there are hallucinations or omissions."
    )
    feedback: str = Field(
        description="Specific instructions for the Simplifier Agent on what facts to correct or what core information is missing. Empty string if accurate."
    )

def node_fact_checker(state: dict) -> dict:
    print("="*20)
    print(" FACT-CHECKER AGENT ")
    print("="*20)
    
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.0)
    
    fact_checker_agent = llm.with_structured_output(FactCheckResult)

    system_prompt = """You are a strict Medical Fact-Checker and your responsibility is scientific accuracy.
    
    Compare the Current Simplified Text against the Original Text, but pay SPECIAL ATTENTION to the 'Core Information'. 
    The Core Information contains the ground-truth facts (Population, Intervention, Comparison, Outcomes) that MUST be preserved.
    
    Look for:
    1. Omissions: Did the draft leave out any crucial data from the Core Information?
    2. Hallucinations: Did the draft invent data or facts not present in the original text?
    3. Distortion: Are the results or statistical findings exaggerated or minimized?
    
    If the text retains all core facts, approve it. If you find omissions, hallucinations or distortions, reject it and provide actionable feedback."""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Original Text:\n{complex_text}\n\nCore Information (MUST BE PRESERVED):\n{core_information}\n\nCurrent Simplified Text:\n{current_simplified_text}")
    ])
    
    chain = prompt | fact_checker_agent
    
    result = chain.invoke({
        "complex_text": state["complex_text"],
        "core_information": state["core_information"],
        "current_simplified_text": state["current_simplified_text"]
    })
    
    feedback_to_append = []
    if not result.is_accurate:
        feedback_to_append.append(f"[FACT-CHECKER FEEDBACK]: {result.feedback}")
    
    return {
        "is_fact_approved": result.is_accurate, 
        "feedback_history": feedback_to_append
    }