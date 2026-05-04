import os
from unittest import result

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from src.agents.llm_factory import build_chat_llm
from src.agents.step_delay import pause_step_sync


class GuardrailResult(BaseModel):
    is_in_scope: bool = Field(
        description="True when the user's input is a biomedical or medical text that can be simplified by the system."
    )
    rationale: str = Field(
        description="Short explanation of why the input is in scope or out of scope."
    )
    refusal_message: str = Field(
        description="Polite fallback message for out-of-scope inputs. Leave empty when is_in_scope is True."
    )


def node_guardrail(state: dict) -> dict:
    # llm = build_chat_llm(
    #     temperature=0.0,
    #     model=os.getenv("GUARDRAIL_MODEL") or None,
    #     provider=os.getenv("GUARDRAIL_PROVIDER") or None,
    # )
    # guardrail_agent = llm.with_structured_output(GuardrailResult)

    # system_prompt_guardrail = (
    #     "You are a strict input guardrail for a Medical Plain Language Simplifier. "
    #     "Your job is to decide whether the user's input should be processed by the simplification workflow.\n\n"
    #     "ACCEPT ONLY if the text is a biomedical, clinical, medical, or health-science passage that can be simplified for a lay audience. "
    #     "Examples of acceptable inputs include medical abstracts, clinical summaries, patient education content, and biomedical research descriptions.\n\n"
    #     "REJECT if the input is unrelated to medicine or health, asks for a different task, is a generic conversation, or is clearly outside the system's scope.\n\n"
    #     "If you reject the input, provide a short, polite refusal_message that tells the user to provide a medical abstract or similar health-related text. "
    #     "If you accept the input, set refusal_message to an empty string."
    # )

    # human_prompt_guardrail = (
    #     "Evaluate the following user input and decide whether it is in scope for the Medical Plain Language Simplifier.\n\n"
    #     "---\n"
    #     "INPUT:\n"
    #     "{complex_text}\n\n"
    #     "---\n"
    #     "Return the structured decision."
    # )

    # prompt_guardrail = ChatPromptTemplate.from_messages([
    #     ("system", system_prompt_guardrail),
    #     ("human", human_prompt_guardrail),
    # ])

    # chain = prompt_guardrail | guardrail_agent

    # try:
    #     result: GuardrailResult = chain.invoke({"complex_text": state["complex_text"]})
    # except Exception as exc:
    #     refusal_message = (
    #         "I can only simplify medical or biomedical texts. Please provide a medical abstract or a health-related passage."
    #     )
    #     pause_step_sync()
    #     return {
    #         "is_input_in_scope": False,
    #         "guardrail_triggered": True,
    #         "guardrail_rationale": f"Guardrail evaluation failed: {exc}",
    #         "guardrail_message": refusal_message,
    #         "current_simplified_text": refusal_message,
    #         "term_explanations": {},
    #         "is_approved": False,
    #     }

    # refusal_message = result.refusal_message.strip()
    # in_scope = result.is_in_scope

    # if not in_scope and not refusal_message:
    #     refusal_message = (
    #         "I can only simplify medical or biomedical texts. Please provide a medical abstract or a health-related passage."
    #     )

    result = GuardrailResult(
        is_in_scope=False,
        rationale="Guardrail is currently disabled, so all inputs are accepted by default.",
        refusal_message="",
    )
    in_scope = result.is_in_scope
    refusal_message = result.refusal_message.strip()

    updates = {
        "is_input_in_scope": in_scope,
        "guardrail_triggered": not in_scope,
        "guardrail_rationale": result.rationale,
        "guardrail_message": refusal_message,
    }

    if not in_scope:
        updates.update(
            {
                "current_simplified_text": refusal_message,
                "term_explanations": {},
                "is_approved": False,
            }
        )

    pause_step_sync()
    return updates
