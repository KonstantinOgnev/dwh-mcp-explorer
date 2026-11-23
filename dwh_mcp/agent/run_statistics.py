import math


def latency_summary(values):
    """Nearest-rank percentiles for recorded durations in milliseconds."""
    samples = sorted(values)

    if any(
        not isinstance(value, (int, float))
        or isinstance(value, bool)
        or not math.isfinite(value)
        or value < 0
        for value in samples
    ):
        raise ValueError("Durations must be finite non-negative numbers")

    if not samples:
        return {
            "count": 0,
            "p50_ms": None,
            "p95_ms": None,
            "max_ms": None,
        }

    def percentile(fraction):
        index = math.ceil(fraction * len(samples)) - 1
        return round(samples[index], 3)

    return {
        "count": len(samples),
        "p50_ms": percentile(0.50),
        "p95_ms": percentile(0.95),
        "max_ms": round(samples[-1], 3),
    }


def estimate_cost(input_tokens, output_tokens, input_rate, output_rate):
    """Estimate USD cost using configured prices per million tokens."""
    if input_rate is None or output_rate is None:
        return None

    for rate in (input_rate, output_rate):
        if not math.isfinite(rate) or rate < 0:
            raise ValueError("Token prices must be finite and non-negative")

    return round(
        (
            input_tokens * input_rate
            + output_tokens * output_rate
        ) / 1_000_000,
        8,
    )