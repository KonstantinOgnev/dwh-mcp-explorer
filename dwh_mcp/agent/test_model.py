from anthropic import Anthropic, APIStatusError
from dwh_mcp.agent.config import load_agent_config


def main():
    config = load_agent_config()

    with Anthropic(
        api_key=config.api_key,
        max_retries=0,
        timeout=60.0,
    ) as client:
        try:
            response = client.messages.create(
                model=config.model,
                max_tokens=256,
                messages=[
                    {
                        "role": "user",
                        "content": "Reply with exactly: API connection OK",
                    }
                ],
            )
        except APIStatusError as error:
            print(f"API error: HTTP {error.status_code}")
            print(error.message)
            return

        for block in response.content:
            if block.type == "text":
                print(block.text)

        print("Model:", response.model)
        print("Stop reason:", response.stop_reason)
        print("Input tokens:", response.usage.input_tokens)
        print("Output tokens:", response.usage.output_tokens)


if __name__ == "__main__":
    main()