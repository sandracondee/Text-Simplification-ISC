import os
import asyncio
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from src.agents.llm_factory import build_chat_llm
from src.tools.metrics import evaluator
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain.agents import create_agent

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

async def node_readability_evaluator(state: dict) -> dict:

    client = MultiServerMCPClient({
        "metrics_server": {
            "url": "http://127.0.0.1:8020/mcp/",
            "transport": "streamable_http"
        }
    })

    try:
        mcp_tools = await client.get_tools()

        llm = build_chat_llm(temperature=0.3, 
                             model=os.getenv("READABILITY_EVALUATOR_MODEL") or None, 
                             provider=os.getenv("READABILITY_EVALUATOR_PROVIDER") or None)

        agent = create_react_agent(
            model=llm, 
            tools=mcp_tools, 
            response_format=ReadabilityResult # Requiere LangGraph actualizado
        )
        system_prompt = """You are an expert NLP Quality Evaluator and your goal is to ensure a medical text is accessible to general audience.
                You MUST use the `calculate_metrics` tool first to get SARI, BLEU, and BERTScore_F1.
                
                EVALUATION CRITERIA:
                1. SARI & BERTScore: SARI can be naturally lower (15-25 is normal) because clinical terms cannot be deleted. Check if BERTScore > 0.2 to ensure no medical facts were altered.
                2. Contextual Vocabulary (CRITICAL TOLERANCE): The target audience are not children. 
                - YOU MUST ALLOW common disease names, standard trial terms (e.g., "placebo", "morbidity"), and specific metrics IF they are briefly contextualized (e.g., "HbA1c, a measurement of glucose control").
                - DO NOT reject a simplification just because it contains these words.
                - You should ONLY penalize bureaucratic academic phrasing (e.g., "allocation concealment") or overly complex statistical jargon (e.g., "95% CI 0.57 to 0.86") if left unsimplified.

                DECISION RULES:
                - APPROVE (is_readable=True) IF: The text resembles a standard medical summary. It flows naturally, explains highly obscure jargon, but rightly retains necessary clinical terminology and disease names. 
                - REJECT (is_readable=False) IF: The text is basically a copy of the academic abstract, retaining dense statistical brackets, bureaucratic study design jargon without explanation, or if the metrics drop indicating a loss of facts.
                
                FEEDBACK INSTRUCTIONS:
                If you reject the draft, your feedback must be specific and actionable.
                You MUST list the exact words, acronyms or sentences that caused the rejection."""
                
        # 4. Modificamos el prompt del usuario para inyectar las 3 variables 
        # que el modelo necesita obligatoriamente para usar la herramienta MCP
        user_prompt = f"""
        Current simplified text: {state["current_simplified_text"]}
        
        DATA REQUIRED FOR YOUR TOOL:
        To use the `calculate_metrics` tool properly, you must use these exact references:
        - complex_text: {state["complex_text"]}
        - current_simplified_text: {state["current_simplified_text"]}
        - reference_text: {state["reference_text"]}
        """
        
        # 5. Invocamos el agente
        response = await agent.ainvoke({
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        })
        
        # En LangGraph, cuando usas response_format, el objeto final tipado 
        # se guarda en la clave "structured_response" de la salida del agente.
        result: ReadabilityResult = response["structured_response"]
        
        feedback_to_append = []
        if not result.is_readable:
            feedback_to_append.append(f"[READABILITY EVALUATOR FEEDBACK]: {result.readability_feedback}")

        return {
            "is_readability_approved": result.is_readable, 
            "feedback_history": feedback_to_append,
            "current_metrics": result.metrics_report
        }
    except Exception as e:
        print(f"Error in readability evaluator: {e}")
        return {
            "is_readability_approved": False, 
            "feedback_history": [],
            "current_metrics": {}
        }