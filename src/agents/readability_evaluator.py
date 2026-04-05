from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from src.tools.metrics import evaluator
from langchain_core.tools import tool

class ReadabilityResult(BaseModel):
    is_readable: bool = Field(
        description="True if metrics are acceptable and no unexplained jargon is found. False otherwise."
    )
    readability_feedback: str = Field(
        description="Specific instructions for the Simplifier Agent on what terms to explain or sentences to simplify. Empty string if everithing is perfect."
    )
    metrics_report: dict = Field(
        description="The SARI, BLEU, and BERTScore values obtained from the tool."
        )

def node_readability_evaluator(state: dict) -> dict:
    print("="*20)
    print(" READABILITY EVALUATOR AGENT ")
    print("="*20)

    @tool
    def calculate_metrics(simplified_text_to_evaluate: str) -> dict:
        """
        Use this tool to calculate SARI, BLEU, and BERTScore metrics for the current simplified text.
        You MUST provide the exact text of the current simplified text you want to evaluate.
        """
        # We access complex_text and reference_text directly from the GraphState
        return evaluator.calc_simplification_metrics(
            complex_text=state["complex_text"],
            current_simplified_text=simplified_text_to_evaluate,
            reference_text=state["reference_text"]
        )
    
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0.0)
    
    llm_with_tools = llm.bind_tools([calculate_metrics])
    readability_agent = llm_with_tools.with_structured_output(ReadabilityResult)
    
    system_prompt = """You are an expert NLP Quality Evaluator.
    You MUST use the `calculate_metrics` tool first to get SARI, BLEU, and BERTScore_F1.
    
    Evaluation Rules:
    1. Check the metric results. If SARI is too low, simplification operations were poor.
    2. Read the draft and identify any remaining medical jargon that a layperson wouldn't understand.
    3. If the text is dense or uses complex vocabulary, reject it.
    
    Provide specific feedback based on the metrics and the vocabulary used."""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Current simplified text:\n{current_simplified_text}")
    ])
    
    chain = prompt | readability_agent
    
    result = chain.invoke({
        "current_simplified_text": state["current_simplified_text"]
    })
    
    feedback_to_append = []
    if not result.is_readable:
        feedback_to_append.append(f"[READABILITY EVALUATOR FEEDBACK]: {result.readability_feedback}")

    return {
        "is_readability_approved": result.is_readable, 
        "feedback_history": feedback_to_append,
        "current_metrics": result.metrics_report
    }