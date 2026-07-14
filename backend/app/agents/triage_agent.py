from functools import lru_cache

from langchain.agents import create_agent

from app.llm.model import get_llm
from app.prompts.triage_prompt import TRIAGE_SYSTEM_PROMPT
from app.tools.authentication_tools import authenticate_customer
from app.tools.conversation_tools import finish_conversation


@lru_cache
def get_triage_agent():
    return create_agent(
        model=get_llm(),
        tools=[
            authenticate_customer,
            finish_conversation,
        ],
        system_prompt=TRIAGE_SYSTEM_PROMPT,
        name="triage_agent",
    )
