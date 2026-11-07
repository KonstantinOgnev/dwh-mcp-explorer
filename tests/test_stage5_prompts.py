
import asyncio

from mcp import Client
from server import mcp


async def main():
    async with Client(mcp) as client:
        response = await client.list_prompts()

        prompt_names = {
            prompt.name
            for prompt in response.prompts
        }

        assert "investigate_dwh_table" in prompt_names

        result = await client.get_prompt(
            "investigate_dwh_table",
            {
                "schema": "gold",
                "table": "fact_orders",
                "filename": "fact_orders.sql"
            }
        )

        assert len(result.messages) == 1

        message = result.messages[0]

        assert message.role == "user"
        assert message.content.type == "text"

        prompt_text = message.content.text

        assert "gold.fact_orders" in prompt_text
        assert "fact_orders.sql" in prompt_text
        assert "investigate_dwh_object" in prompt_text
        assert "partial or failed" in prompt_text

        print("PASS: MCP prompt registered")
        print("PASS: MCP prompt rendered")
        print("PASS: Investigation instructions validated")
        print("STAGE 5.3.4.3 MCP PROMPTS: PASSED")


if __name__ == "__main__":
    asyncio.run(main())
