from functools import lru_cache

from langchain.agents import create_agent

from app.llm.model import get_llm
from app.prompts.credit_prompt import CREDIT_SYSTEM_PROMPT
from app.tools.conversation_tools import finish_conversation
from app.tools.credit_tools import (
    get_customer_credit_limit,
    request_credit_limit_increase,
)


@lru_cache
def get_credit_agent():
    return create_agent(
        model=get_llm(),
        tools=[
            get_customer_credit_limit,
            request_credit_limit_increase,
            finish_conversation,
        ],
        system_prompt=CREDIT_SYSTEM_PROMPT,
        name="credit_agent",
    )
