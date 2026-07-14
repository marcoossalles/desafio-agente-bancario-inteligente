from functools import lru_cache

from langchain.agents import create_agent

from app.llm.model import get_llm
from app.prompts.credit_interview_prompt import (
    CREDIT_INTERVIEW_SYSTEM_PROMPT,
)
from app.tools.conversation_tools import finish_conversation
from app.tools.score_tools import calculate_and_update_credit_score


@lru_cache
def get_credit_interview_agent():
    return create_agent(
        model=get_llm(),
        tools=[
            calculate_and_update_credit_score,
            finish_conversation,
        ],
        system_prompt=CREDIT_INTERVIEW_SYSTEM_PROMPT,
        name="credit_interview_agent",
    )
