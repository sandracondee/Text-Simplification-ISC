import os
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import create_agent
from pydantic import BaseModel, Field
from typing import List
from src.agents.llm_factory import build_chat_llm
from src.mcp.mcp_manager import mcp_manager

class GlossaryTerm(BaseModel):
    term: str = Field(description="The complex medical term extracted from the text.")
    url: str = Field(description="A valid, real URL pointing to a patient-friendly definition of the term.")

class GlossaryResult(BaseModel):
    glossary: List[GlossaryTerm] = Field(
        description="A list of 3 to 10 complex words and their explanations.",
        min_length=3,
        max_length=10
    )

async def node_glossary_builder(state: dict) -> dict:

    try:
        mcp_tools = await mcp_manager.get_tools_for_agent(["search_server"])
        
        llm = build_chat_llm(temperature=0.2, 
                             model=os.getenv("GLOSSARY_MODEL") or None, 
                             provider=os.getenv("GLOSSARY_PROVIDER") or None)

        agent = create_agent(
            model=llm, 
            tools=mcp_tools, 
            response_format=GlossaryResult
        )

        system_prompt_glossary = (
            "You are an expert Medical Glossary Builder. "
            "Your task is to identify between 3 and 10 complex or technical medical terms in a simplified text and provide a patient-friendly explanation for each.\n\n"
            "INSTRUCTIONS:\n"
            "1. Read the text and extract 3 to 10 words that a layperson might still find challenging.\n"
            "2. For EACH word, you MUST use your web search tool to find its definition.\n"
            "3. Read the search results and write a short, accessible explanation (1 to 2 sentences max) for the term.\n"
            "4. Do NOT return the URL. Return the term and your synthesized explanation.\n"
            "5. These explanations will be displayed as interactive tooltips in a web interface, so they must be concise, accurate, and easy to read."
        )

        human_prompt_glossary = (
            "Extract 3 to 10 complex words from this text, search for their meanings using your tool, and write a short explanation for each:\n\n"
            "---\n"
            "TEXT:\n"
            "{current_simplified_text}\n\n"
            "---\n"
            "Return the structured glossary."
        )

        prompt_glossary = ChatPromptTemplate.from_messages([
            ("system", system_prompt_glossary),
            ("human", human_prompt_glossary)
        ])

        messages = prompt_glossary.format_messages(
            current_simplified_text=state["current_simplified_text"]
        )
        
        response = await agent.ainvoke({"messages": messages})
        
        result: GlossaryResult = response["structured_response"]

        glossary_dict = {item.term: item.explanation for item in result.glossary}

        return {
            "glossary_data": glossary_dict # Actualizamos el estado con el glosario
        }
        
    except Exception as e:
        print(f"Error in glossary builder: {e}")
        return state