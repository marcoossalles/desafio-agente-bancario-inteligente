from functools import lru_cache

from langchain.agents import create_agent

from app.llm.model import get_llm
from app.prompts.exchange_prompt import EXCHANGE_SYSTEM_PROMPT
from app.tools.conversation_tools import finish_conversation
from app.tools.exchange_tools import get_exchange_rate


@lru_cache
def get_exchange_agent():
    return create_agent(
        model=get_llm(),
        tools=[
            get_exchange_rate,
            finish_conversation,
        ],
        system_prompt=EXCHANGE_SYSTEM_PROMPT,
        name="exchange_agent",
    )
