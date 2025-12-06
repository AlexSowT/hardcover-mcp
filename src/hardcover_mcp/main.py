from fastmcp import FastMCP
from hardcover_mcp.server.books import get_books_server
from hardcover_mcp.server.users import get_users_server
from hardcover_mcp.server.series import get_series_server
from hardcover_mcp.hardcover_client import HardcoverClient
import asyncio
import os

mcp = FastMCP(
    name="HardcoverMCP",
    instructions=(
        "Read-only Hardcover GraphQL access for books, users, and series. "
        "Requires HARDCOVER_API_KEY (Bearer token) and never performs mutations. "
        "Tools are namespaced under books.*, users.*, and series.*."
    ),
    version="0.1",
)


async def setup():
    api_key = os.environ.get("HARDCOVER_API_KEY")
    if not api_key:
        raise RuntimeError(
            "HARDCOVER_API_KEY environment variable is required for HardcoverMCP. One can be created at 'https://hardcover.app/account/api'"
        )

    if not api_key.lower().startswith("bearer "):
        api_key = f"Bearer {api_key}"

    client = HardcoverClient(auth_header=api_key)

    await mcp.import_server(get_books_server(client), prefix="books")
    await mcp.import_server(get_users_server(client), prefix="users")
    await mcp.import_server(get_series_server(client), prefix="series")


@mcp.resource(
    uri="data://hardcover/tag-categories",
    description="Static mapping of tag category IDs used by the search tools.",
)
async def tag_categories():
    return {
        "genre": 1,
        "general_tags": 2,
        "content_warnings": 3,
        "mood": 4,
        "pace": 37,
    }


@mcp.resource(
    uri="data://hardcover/book-statuses",
    description="User book status identifiers used by user.* tools.",
)
async def book_statuses():
    return {
        "want_to_read": 1,
        "currently_reading": 2,
        "read": 3,
        "paused": 4,
        "dnf": 5,
    }


@mcp.prompt(
    name="hardcover/fantasy-this-year",
    description="Guide to find fantasy books released this year using the books.* tools.",
)
async def fantasy_this_year_prompt():
    return (
        "Search for fantasy books released this calendar year. "
        "Prefer books.get_books_by_genre with genre ['Fantasy'], "
        "rating_minimum >= 50 ratings, and min_year/max_year set to the current year."
    )


@mcp.prompt(
    name="hardcover/similar-to-my-reads",
    description="Find books similar to the user's read shelf using tag overlap.",
)
async def similar_to_my_reads_prompt():
    return (
        "1) Call users.get_user_books_read to fetch the read shelf.\n"
        "2) Extract a small set of representative tags (genre/mood/content_warnings) from those books.\n"
        "3) Use books.get_books_by_genre / books.get_books_by_mood / books.get_books_by_tag "
        "with those tags to surface similar titles. Keep limits small (<=10) to avoid throttling."
    )


if __name__ == "__main__":
    asyncio.run(setup())
    mcp.run()
