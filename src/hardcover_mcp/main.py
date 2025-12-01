from fastmcp import FastMCP
from hardcover_mcp.server.books import get_books_server
from hardcover_mcp.hardcover_client import HardcoverClient
import asyncio

mcp = FastMCP(
    name="HardcoverMCP",
    instructions="",
    version="0.1",
)


@mcp.tool
def test():
    return "test"


async def setup():
    client = HardcoverClient(
        auth_header="Bearer REDACTED_TOKEN"
    )

    await mcp.import_server(get_books_server(client), prefix="books")


if __name__ == "__main__":
    asyncio.run(setup())
    mcp.run()
