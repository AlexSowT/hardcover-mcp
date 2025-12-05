from fastmcp import FastMCP
from hardcover_mcp.server.books import get_books_server
from hardcover_mcp.server.users import get_users_server
from hardcover_mcp.server.series import get_series_server
from hardcover_mcp.hardcover_client import HardcoverClient
import asyncio
import os

mcp = FastMCP(
    name="HardcoverMCP",
    instructions="",
    version="0.1",
)


async def setup():
    api_key = os.environ.get("HARDCOVER_API_KEY")
    if not api_key:
        raise RuntimeError("HARDCOVER_API_KEY environment variable is required for HardcoverMCP. One can be created at 'https://hardcover.app/account/api'")

    if not api_key.lower().startswith("bearer "):
        api_key = f"Bearer {api_key}"

    client = HardcoverClient(auth_header=api_key)

    await mcp.import_server(get_books_server(client), prefix="books")
    await mcp.import_server(get_users_server(client), prefix="users")
    await mcp.import_server(get_series_server(client), prefix="series")


if __name__ == "__main__":
    asyncio.run(setup())
    mcp.run()
