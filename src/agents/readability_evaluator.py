import os
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from src.agents.llm_factory import build_chat_llm
from src.mcp.mcp_manager import mcp_manager
from src.agents.step_delay import pause_step_async
from langchain.agents import create_agent
from langchain_core.tools import tool

class ReadabilityResult(BaseModel):
    metrics_report: dict = Field(description="The SARI, BLEU, BERTScore and FKGL values obtained from the tool.")
    is_readability_approved: bool = Field(description="True if the text meets the readability standards for a general audience and metrics are acceptable. False otherwise.")
    feedback: str = Field(description="If is_readability_approved is False, provide specific instructions to fix it (e.g., 'Make sentences shorter in paragraph 2'). If True, leave empty.")

async def node_readability_evaluator(state: dict) -> dict:

    try:
    #     mcp_tools = await mcp_manager.get_tools_for_agent(["metrics_server"])
    #     mcp_metrics_tool = mcp_tools[0]
        
    #     @tool
    #     async def calculate_metrics_for_current_draft() -> dict:
    #         """
    #         Call this tool to calculate objective metrics: SARI, BLEU, BERTScore and FKGL.
    #         You do NOT need to provide the text arguments, the system will inject them automatically.
    #         """

    #         return await mcp_metrics_tool.ainvoke({
    #             "complex_text": state.get("complex_text", ""),
    #             "current_simplified_text": state.get("current_simplified_text", ""),
    #             "reference_text": state.get("reference_text", "")
    #         })

    #     llm = build_chat_llm(temperature=0.0, 
    #                          model=os.getenv("READABILITY_EVALUATOR_MODEL") or None, 
    #                          provider=os.getenv("READABILITY_EVALUATOR_PROVIDER") or None)

    #     agent = create_agent(
    #         model=llm, 
    #         tools=[calculate_metrics_for_current_draft], 
    #         response_format=ReadabilityResult
    #     )
        
    #     system_prompt_readability = (
    #         "You are an expert Readability Evaluator for Medical Plain Language. "
    #         "Your task is to assess whether a simplified medical text is accessible and easy to understand for the general public without medical training.\n\n"
    #         "INSTRUCTIONS:\n"
    #         "1. Tool Usage: You MUST use the readability tools provided to you to calculate objective metrics: SARI, BLEU, BERTScore, and FKGL.\n"
    #         "2. SARI IS THE ONLY METRIC THAT MATTERS: The ONLY quantitative threshold you must enforce is SARI. If the SARI score is lower than 35, you MUST fail the text automatically.\n"
    #         "3. Qualitative Assessment: Regardless of the SARI score, read the text yourself. Is it genuinely understandable for a layperson? Does it sound natural? If it is confusing, highly academic, or robotic, you must fail it.\n"
    #         "4. Verdict: Based ONLY on the SARI threshold (>35) and your qualitative assessment, decide if the text passes. If it fails, set 'is_readability_approved' to False and write clear, actionable instructions in 'feedback' (e.g., 'SARI is below 35, simplify vocabulary', or 'Text sounds too academic, use everyday language').\n"
    #         "5. Do NOT evaluate the clinical accuracy or factual correctness of the text."
    #     )

    #     human_prompt_readability = (
    #         "Evaluate the readability of the following simplified text:\n\n"
    #         "---\n"
    #         "SIMPLIFIED TEXT:\n"
    #         "{current_simplified_text}\n\n"
    #         "---\n"
    #         "First, use your tools to analyze the text. Then, return the final evaluation using the structured format."
    #     )
        
    #     prompt_readability = ChatPromptTemplate.from_messages([
    #         ("system", system_prompt_readability),
    #         ("human", human_prompt_readability)
    #     ])

    #     messages = prompt_readability.format_messages(
    #         current_simplified_text=state["current_simplified_text"]
    #     )

    #     response = await agent.ainvoke({
    #         "messages": messages
    #     })

        response = {
            "structured_response": ReadabilityResult(
                metrics_report={
                    "SARI": 40.5,
                    "BLEU": 0.25,
                    "BERTScore": 0.85,
                    "FKGL": 8.2
                },
                is_readability_approved=True,
                feedback="Hola estoy probando el evaluador de legibilidad"
            )
        } # --- MOCK PARA TESTING ---
        
        result: ReadabilityResult = response["structured_response"]
        
        feedback_to_append = []
        if not result.is_readability_approved:
            feedback_to_append.append(f"[READABILITY EVALUATOR FEEDBACK]: {result.feedback}")

        await pause_step_async()

        return {
            "readability_evaluator_feedback": result.feedback,
            "is_readability_approved": result.is_readability_approved, 
            "feedback_history": feedback_to_append,
            "current_metrics": result.metrics_report
        }
    
    except Exception as e:
        print(f"Error in readability evaluator: {e}")
        await pause_step_async()
        return {
            "readability_evaluator_feedback": f"Error during evaluation: {str(e)}",
            "is_readability_approved": False, 
            "feedback_history": [],
            "current_metrics": {}
        }