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
        auth_header="Bearer eyJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJIYXJkY292ZXIiLCJ2ZXJzaW9uIjoiOCIsImp0aSI6IjBmZWYzMDdkLTJlZWEtNGY5Yi1hMmEwLTRmN2Q4ZmUxYzVjMCIsImFwcGxpY2F0aW9uSWQiOjIsInN1YiI6IjU2MjI5IiwiYXVkIjoiMSIsImlkIjoiNTYyMjkiLCJsb2dnZWRJbiI6dHJ1ZSwiaWF0IjoxNzY0MzgyMzUyLCJleHAiOjE3OTU5MTgzNTIsImh0dHBzOi8vaGFzdXJhLmlvL2p3dC9jbGFpbXMiOnsieC1oYXN1cmEtYWxsb3dlZC1yb2xlcyI6WyJ1c2VyIl0sIngtaGFzdXJhLWRlZmF1bHQtcm9sZSI6InVzZXIiLCJ4LWhhc3VyYS1yb2xlIjoidXNlciIsIlgtaGFzdXJhLXVzZXItaWQiOiI1NjIyOSJ9LCJ1c2VyIjp7ImlkIjo1NjIyOX19.2pLp3N9kW8ozifkKjQvlUFn7XYyfTk5JOLwkE-o471M"
    )

    await mcp.import_server(get_books_server(client), prefix="books")


if __name__ == "__main__":
    asyncio.run(setup())
    mcp.run()
