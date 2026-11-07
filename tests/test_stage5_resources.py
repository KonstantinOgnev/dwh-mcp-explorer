
import asyncio
import json

from mcp import Client
from server import mcp


async def main():
    async with Client(mcp) as client:
        resources = await client.list_resources()

        uris = {str(item.uri) for item in resources.resources}

        assert "dwh://explorer/capabilities" in uris

        result = await client.read_resource(
            "dwh://explorer/capabilities"
        )

        data = json.loads(result.contents[0].text)

        assert data["service"] == "DWH Metadata Explorer"
        assert data["sql_execution"] is False
        assert "composite_investigation" in data["capabilities"]

        print("PASS: MCP resource registered")
        print("PASS: MCP resource readable")
        print("PASS: DWH capabilities validated")
        print("STAGE 5.3.4.1 STATIC RESOURCE: PASSED")


if __name__ == "__main__":
    asyncio.run(main())
