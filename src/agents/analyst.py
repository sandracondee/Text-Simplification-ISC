from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from src.agents.llm_factory import build_chat_llm

class AnalystResult(BaseModel):
    core_information: str = Field(
        description="The most clinically relevant and critical information extracted from the original text. " \
        "This includes primary medical findings, essential context, vital safety warnings or side effects, and conclusions that must not be lost or altered during simplification."
    )

def node_analyst(state: dict) -> dict:
    print("="*40)
    print(" ANALYST AGENT ")
    print("="*40)

    llm = build_chat_llm(temperature=0.3)

    extractor_agent = llm.with_structured_output(AnalystResult)
    
    system_prompt = """You are an expert Clinical Data Analyst specialized in biomedical literature. 
    Your task is to analyze the original medical text and extract its core components to ensure no critical data is lost in the later simplification.

    Focus on this main points:
    - Population/Patient/Problem: Who was studied?
    - Intervention: What was the treatment or action?
    - Comparison: What was the control or alternative?
    - Outcomes: What were the main results, statistical findings, and side effects?

    Additionally, list any highly technical medical terms (jargon) that appear in the text.
    DO NOT simplify the text. Only extract and organize the facts."""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Original Complex Text:\n{complex_text}")
    ])
    
    chain = prompt | extractor_agent
    
    result = chain.invoke({
        "complex_text": state["complex_text"]
    })
    
    return {
        "core_information": result.core_information
    }