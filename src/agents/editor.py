import os
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from src.agents.llm_factory import build_chat_llm
from src.agents.step_delay import pause_step_sync


class EditorResult(BaseModel):
    corrected_text: str = Field(description="The final corrected version of the simplified text.")


def node_editor(state: dict) -> dict:
    print("=" * 40)
    print(" THE EDITOR ")
    print("=" * 40)

    # llm = build_chat_llm(temperature=0.2, model=os.getenv("EDITOR_MODEL") or None, provider=os.getenv("EDITOR_PROVIDER") or None)
    # editor_agent = llm.with_structured_output(EditorResult)

    # feedback = "\n".join(state["feedback_history"])

    # system_prompt_editor = (
    #     "You are an expert Medical Text Editor. Your job is to refine a simplified biomedical abstract based strictly on feedback from expert auditors.\n\n"
    #     "INSTRUCTIONS:\n"
    #     "1. You will receive a 'Simplified Text' and an 'Audit Feedback' report detailing factual errors or readability issues.\n"
    #     "2. Your ONLY task is to correct the specific issues mentioned in the feedback.\n"
    #     "3. DO NOT rewrite the entire text from scratch. Keep the original structure, style, formatting and tone intact as much as possible.\n"
    #     "4. If a number or fact is reported as incorrect, update it exactly as requested.\n"
    #     "5. If a sentence is flagged as too complex (e.g., high SARI), simplify the vocabulary or split the sentence, but keep the core meaning."
    # )

    # human_prompt_editor = (
    #     "Please correct the following text based on the audit feedback.\n\n"
    #     "--- SIMPLIFIED TEXT ---\n"
    #     "{current_simplified_text}\n\n"
    #     "--- AUDIT FEEDBACK ---\n"
    #     "{feedback_history}\n\n"
    #     "Return only the corrected text. Do NOT include any explanations or justifications, only the final edited version."
    # )

    # prompt_editor = ChatPromptTemplate.from_messages([
    #     ("system", system_prompt_editor),
    #     ("human", human_prompt_editor)
    # ])

    # editor_chain = prompt_editor | editor_agent
    # result: EditorResult = editor_chain.invoke({
    #         "current_simplified_text": state["current_simplified_text"],
    #         "feedback_history": feedback
    #     })


    # TESTING
    result = EditorResult(
        corrected_text="Este es el texto médico simplificado corregido. Se ha generado un mock directo sin llamar a ningún LLM para agilizar el desarrollo y las pruebas."
    )

    pause_step_sync()

    return {
        "current_simplified_text": result.corrected_text,
        "iteration_count": state["iteration_count"] + 1,
        "feedback_history": [],
        "is_fact_approved": False,
        "is_readability_approved": False
    }