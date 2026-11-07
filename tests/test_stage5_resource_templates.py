
import asyncio
import json

from mcp import Client
from server import mcp


async def main():
    async with Client(mcp) as client:
        templates = await client.list_resource_templates()

        template_uris = {
            str(item.uri_template)
            for item in templates.resource_templates
        }

        assert (
            "dwh://tables/{schema}/{table}"
            in template_uris
        )

        result = await client.read_resource(
            "dwh://tables/gold/fact_orders"
        )

        assert len(result.contents) == 1
        data = json.loads(result.contents[0].text)

        assert data["object"] == "gold.fact_orders"
        assert data["source_type"] == "postgresql"

        columns = {col["name"] for col in data["columns"]}

        assert columns == {
            "order_key",
            "order_id",
            "customer_key",
            "order_date",
            "amount"
        }

        assert data["primary_keys"]
        assert data["foreign_keys"]

        print("PASS: Dynamic resource template registered")
        print("PASS: PostgreSQL metadata resource readable")
        print("PASS: Target columns and keys validated")
        print("STAGE 5.3.4.2 DYNAMIC RESOURCE: PASSED")


if __name__ == "__main__":
    asyncio.run(main())
