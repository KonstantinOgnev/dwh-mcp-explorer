import os
from dataclasses import dataclass, field

from dotenv import load_dotenv


@dataclass(frozen=True)
class AgentConfig:
    api_key: str = field(repr=False)
    model: str
    max_steps: int = 10
    max_tokens: int = 8192


def load_agent_config() -> AgentConfig:
    load_dotenv()

    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    model = os.getenv("DWH_AGENT_MODEL", "").strip()

    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY is not configured")

    if not model:
        raise ValueError("DWH_AGENT_MODEL is not configured")

    return AgentConfig(api_key=api_key, model=model)