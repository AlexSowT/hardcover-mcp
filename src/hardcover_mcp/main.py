from fastmcp import FastMCP
from hardcover_mcp.server.books import get_books_server
from hardcover_mcp.server.users import get_users_server
from hardcover_mcp.hardcover_client import HardcoverClient
import asyncio
import os

mcp = FastMCP(
    name="HardcoverMCP",
    instructions="",
    version="0.1",
)


@mcp.tool
def test():
    return "test"

async def setup():
    api_key = os.environ.get("API_KEY")
    print(api_key)
    if not api_key:
        raise RuntimeError("API_KEY environment variable is required for HardcoverMCP")

    if not api_key.lower().startswith("bearer "):
        api_key = f"Bearer {api_key}"

    client = HardcoverClient(auth_header=api_key)

    await mcp.import_server(get_books_server(client), prefix="books")
    await mcp.import_server(get_users_server(client), prefix="users")


if __name__ == "__main__":
    asyncio.run(setup())
    mcp.run()
