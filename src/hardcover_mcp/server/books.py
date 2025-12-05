from fastmcp import FastMCP, Context
from fastmcp.exceptions import ToolError
from hardcover_mcp.hardcover_client import HardcoverClient
from hardcover_mcp.schemas.book import Book
from hardcover_mcp.queries.book import (
    BOOKS_BY_ID_QUERY,
    BOOKS_BY_TITLE_QUERY,
    BOOKS_BY_GENRE_QUERY,
)

mcp = FastMCP(name="BooksMCP")
_client = None


def get_books_server(client: HardcoverClient) -> FastMCP:
    global _client
    _client = client
    return mcp


def parse_book_response(book_data) -> list[Book]:
    if isinstance(book_data, dict):
        books = [book_data]
    else:
        books = book_data

    parsed: list[Book] = []

    for book in books:
        rating = book.get("rating")
        if rating is not None:
            try:
                rating = float(rating)
            except (TypeError, ValueError):
                rating = None

        author_names: list[str] = []
        for contribution in book.get("contributions", []):
            author = (contribution or {}).get("author") or {}
            name = author.get("name")
            if name:
                author_names.append(name)

        parsed.append(
            Book(
                title=book.get("title", ""),
                release_year=book.get("release_year"),
                rating=rating,
                ratings_count=book.get("ratings_count", 0),
                reviews_count=book.get("reviews_count", 0),
                author_names=author_names,
                description=book.get("description", ""),
                users_read_count=book.get("users_read_count", 0),
            )
        )

    return parsed


@mcp.tool(
    description="""Search the Hardcover database to get a book by hardcover book ID. 
                    Returns infomation such as name, author, descirpitob, reviews, and the mood and genre of the book.
                    Important: This tool should only be used with a Hardcover ID.""",
    tags={"books", "search"},
    annotations={"title": "Search books by Title", "readOnlyHint": True},
    enabled=False

)
async def get_book_by_id(id: int, ctx: Context) -> list[Book]:
    if not isinstance(id, int) or id < 1:
        raise TypeError(f"Book ID must be a positive integer. id: {id}")

    result = await _client.query(BOOKS_BY_ID_QUERY, variables={"id": id}, ctx=ctx)
    book_data = result["books"]

    return parse_book_response(book_data)


@mcp.tool(
    description="""Search the Hardcover database to get a book by the provided name. 
                    Returns infomation such as name, author, descirpitob, reviews, and the mood and genre of the book""",
    tags={"books", "search"},
    annotations={"title": "Search books by Title", "readOnlyHint": True},
)
async def get_books_by_title(title: str, ctx: Context, tagging_count_minimum: int = 5000):
    if not isinstance(title, str) or not title.strip():
        raise TypeError("Title must be a non-empty string")

    result = await _client.query(
            BOOKS_BY_TITLE_QUERY, variables={"title": title, "tagging_count_minimum": tagging_count_minimum}, ctx=ctx
    )
    await ctx.debug(result)
    book_data = result["books"]

    if len(book_data) == 0:
        # Possible cause for illitication here to find a correct title
        raise ToolError(f"No books found with the title {title}.")

    return parse_book_response(book_data)


@mcp.tool(
    description="""Search the Hardcover database to get a list of books by genre that have a minimum rating count. 
                    Returns infomation such as name, author, descirpitob, reviews, and the mood and genre of the book""",
    tags={"books", "search"},
    annotations={"title": "Search books by Genre", "readOnlyHint": True},
)
async def get_books_by_genre(
    genre: list[str],
    rating_minimum: int = 50,
    limit: int = 5,
    offset: int = 0,
    tagging_count_minimum: int = 5000,
    ctx: Context = None,
):
    # if not isinstance(genre, str) or not genre.strip():
    #   raise TypeError("Genre must be a non-empty string")

    result = await _client.query(
        BOOKS_BY_GENRE_QUERY,
        variables={
            "genre": genre,
            "rating_minimum": rating_minimum,
            "limit": limit,
            "offset": offset,
            "tagging_count_minimum": tagging_count_minimum
        },
        ctx=ctx,
    )
    book_data = result["books"]

    if len(book_data) == 0:
        # Possible cause for illitication here to find a correct title
        raise ToolError(
            f"No books found with the genre {genre} that had over {rating_minimum} ratings."
        )

    return book_data
