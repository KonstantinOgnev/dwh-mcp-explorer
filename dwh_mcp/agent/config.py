import os
from dataclasses import dataclass, field

from dotenv import load_dotenv
import math


@dataclass(frozen=True)
class AgentConfig:
    api_key: str = field(repr=False)
    model: str
    max_steps: int = 10
    max_tokens: int = 8192
    max_tool_calls: int = 8
    input_usd_per_million: float | None = None
    output_usd_per_million: float | None = None

def optional_price(name: str) -> float | None:
    raw = os.getenv(name, "").strip()
    if not raw:
        return None

    value = float(raw)
    if not math.isfinite(value) or value < 0:
        raise ValueError(f"{name} must be finite and non-negative")
    return value

def load_agent_config() -> AgentConfig:
    load_dotenv()

    api_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    model = os.getenv("DWH_AGENT_MODEL", "").strip()

    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY is not configured")

    if not model:
        raise ValueError("DWH_AGENT_MODEL is not configured")

    return AgentConfig(
        api_key=api_key,
        model=model,
        input_usd_per_million=optional_price(
            "DWH_INPUT_USD_PER_MILLION"
        ),
        output_usd_per_million=optional_price(
            "DWH_OUTPUT_USD_PER_MILLION"
        ),
    )