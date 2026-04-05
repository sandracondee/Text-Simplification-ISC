from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

class SimplificationResult(BaseModel):
    current_simplified_text: str = Field(
        description="The resulting plain language summary, ensuring it is accessible to the widest possible audience "
        "(e.g., avoiding local idioms, using universally understood terms, and maintaining clear structures)."
    )

def node_pl_simplifier(state: dict) -> dict:
    print("="*20)
    print(" PLAIN LANGUAGE SIMPLIFIER AGENT ")
    print("="*20)
    
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.3)
    
    simplifier_agent = llm.with_structured_output(SimplificationResult)
    
    system_prompt = """You are a specialized Medical Writer and your target audience is the general public. 
    Your task is to write a Plain Language Summary of the given biomedical abstract.

    RULES:
    1. Use active voice, short sentences, and everyday language.
    2. You MUST preserve all facts listed in the 'Core Information'. Do not omit risks or exaggerate benefits.
    3. Explain any medical jargon clearly.
    4. IF THERE IS FEEDBACK HISTORY: This means your previous simplification was rejected. You MUST read the feedback and strictly adjust your new simplification to fix the errors mentioned."""
    
    feedback = "\n".join(state.get("feedback_history", []))
    if not feedback:
        feedback = "No previous feedback. This is the first simplification."

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", """Original Biomedical Abstract:{complex_text}\n\nCore Information to Preserve:{core_information}\n\n
                    Feedback from Evaluators (Correct these issues):{feedback_history}\n\nWrite the simplified version of the biomedical abstract.""")
    ])
    
    chain = prompt | simplifier_agent
    
    result = chain.invoke({
        "complex_text": state["complex_text"],
        "core_information": state.get("core_information", ""),
        "feedback_history": feedback
    })
    
    return {
        "current_simplified_text": result.current_simplified_text,
        "iteration_count": state.get("iteration_count", 0) + 1
    }