from fastmcp import FastMCP, Context
from fastmcp.exceptions import ToolError
from hardcover_mcp.hardcover_client import HardcoverClient
from hardcover_mcp.schemas.book import Book

mcp = FastMCP(name="BooksMCP")
_client = None


def get_books_server(client: HardcoverClient) -> FastMCP:
    global _client
    _client = client
    return mcp
