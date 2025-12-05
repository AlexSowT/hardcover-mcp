from fastmcp import FastMCP, Context
from fastmcp.exceptions import ToolError
from hardcover_mcp.hardcover_client import HardcoverClient
from hardcover_mcp.queries.series import (
    SERIES_BY_NAME_QUERY,
    SERIES_BY_BOOK_TITLE_QUERY,
    SERIES_NEXT_BOOK_QUERY,
    SERIES_NEXT_BOOK_BY_TITLE_QUERY,
)
from hardcover_mcp.schemas.series import (
    Series,
    SeriesBook,
    SeriesMembership,
    NextInSeries,
)


def _validate_paging(limit: int, offset: int = 0) -> None:
    if not isinstance(limit, int) or limit < 1 or limit > 50:
        raise TypeError("limit must be an integer between 1 and 50")
    if not isinstance(offset, int) or offset < 0:
        raise TypeError("offset must be a non-negative integer")


def _coerce_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _coerce_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_series_books(series_books) -> list[SeriesBook]:
    parsed: list[SeriesBook] = []
    for sb in series_books:
        book_info = (sb or {}).get("book") or {}
        parsed.append(
            SeriesBook(
                position=_coerce_int(sb.get("position")),
                book_id=_coerce_int(book_info.get("id")),
                title=book_info.get("title", ""),
                release_year=_coerce_int(book_info.get("release_year")),
                rating=_coerce_float(book_info.get("rating")),
                ratings_count=_coerce_int(book_info.get("ratings_count")),
            )
        )
    return parsed


def parse_series(series_data) -> list[Series]:
    parsed: list[Series] = []
    for entry in series_data:
        books = parse_series_books(entry.get("book_series", []))
        parsed.append(
            Series(
                id=_coerce_int(entry.get("id")),
                name=entry.get("name", ""),
                slug=entry.get("slug"),
                books_count=_coerce_int(entry.get("books_count")),
                books=books,
            )
        )
    return parsed


def parse_series_memberships(data) -> list[SeriesMembership]:
    parsed: list[SeriesMembership] = []
    for entry in data:
        series_info = (entry or {}).get("series") or {}
        book_info = (entry or {}).get("book") or {}
        parsed.append(
            SeriesMembership(
                position=_coerce_int(entry.get("position")),
                series_id=_coerce_int(series_info.get("id")),
                series_name=series_info.get("name", ""),
                series_slug=series_info.get("slug"),
                book_id=_coerce_int(book_info.get("id")),
                book_title=book_info.get("title", ""),
                book_release_year=_coerce_int(book_info.get("release_year")),
            )
        )
    return parsed


def parse_next_in_series(data, current_book_id: int) -> NextInSeries:
    entry = data[0] if isinstance(data, list) and data else {}
    series_info = (entry or {}).get("series") or {}
    current_position = _coerce_int(entry.get("position"))
    series_books = series_info.get("book_series") or []

    next_book_raw = None
    for sb in series_books:
        book_info = (sb or {}).get("book") or {}
        if _coerce_int(book_info.get("id")) == current_book_id:
            continue
        position = _coerce_int(sb.get("position"))
        if current_position is None or (
            position is not None and position > current_position
        ):
            next_book_raw = sb
            break

    next_book_parsed = parse_series_books([next_book_raw])[0] if next_book_raw else None

    return NextInSeries(
        series_id=_coerce_int(series_info.get("id")),
        series_name=series_info.get("name", ""),
        series_slug=series_info.get("slug"),
        current_position=current_position,
        next_book=next_book_parsed,
    )


def get_series_server(client: HardcoverClient) -> FastMCP:
    """Build a Series server bound to the provided Hardcover client."""
    if client is None:
        raise ToolError("Hardcover client has not been configured")

    mcp = FastMCP(name="SeriesMCP")

    @mcp.tool(
        description="Search series by name.",
        tags={"series", "search"},
        annotations={"title": "Search series by name", "readOnlyHint": True},
    )
    async def get_series_by_name(
        name: str, ctx: Context, limit: int = 5, offset: int = 0
    ) -> list[Series]:
        if not isinstance(name, str) or not name.strip():
            raise TypeError("name must be a non-empty string")
        _validate_paging(limit, offset)

        result = await client.query(
            SERIES_BY_NAME_QUERY,
            variables={"name": name, "limit": limit, "offset": offset},
            ctx=ctx,
        )
        series_list = result["series"]
        if not series_list:
            raise ToolError(f"No series found matching name '{name}'.")
        return parse_series(series_list)

    @mcp.tool(
        description="Find series memberships for a given book title.",
        tags={"series", "search"},
        annotations={"title": "Find series by book title", "readOnlyHint": True},
    )
    async def get_series_by_book_title(
        title: str, ctx: Context, limit: int = 5
    ) -> list[SeriesMembership]:
        if not isinstance(title, str) or not title.strip():
            raise TypeError("title must be a non-empty string")
        _validate_paging(limit, 0)

        result = await client.query(
            SERIES_BY_BOOK_TITLE_QUERY,
            variables={"title": title, "limit": limit},
            ctx=ctx,
        )
        memberships = result["book_series"]
        if not memberships:
            raise ToolError(f"No series memberships found for book title '{title}'.")
        return parse_series_memberships(memberships)

    @mcp.tool(
        description="Get the next book in a series given a book ID.",
        tags={"series", "search"},
        annotations={"title": "Get next book in series", "readOnlyHint": True},
    )
    async def get_next_book_in_series(book_id: int, ctx: Context) -> NextInSeries:
        if not isinstance(book_id, int) or book_id < 1:
            raise TypeError("book_id must be a positive integer")

        result = await client.query(
            SERIES_NEXT_BOOK_QUERY, variables={"book_id": book_id}, ctx=ctx
        )
        series_books = result["book_series"]
        if not series_books:
            raise ToolError(f"No series information found for book id {book_id}.")

        parsed = parse_next_in_series(series_books, current_book_id=book_id)
        if parsed.next_book is None:
            raise ToolError(f"No next book found in the series for book id {book_id}.")
        return parsed

    @mcp.tool(
        description="Get the next book in a series given a book title.",
        tags={"series", "search"},
        annotations={"title": "Get next book in series by title", "readOnlyHint": True},
    )
    async def get_next_book_in_series_by_title(
        title: str, ctx: Context
    ) -> NextInSeries:
        if not isinstance(title, str) or not title.strip():
            raise TypeError("title must be a non-empty string")

        result = await client.query(
            SERIES_NEXT_BOOK_BY_TITLE_QUERY, variables={"title": title.strip()}, ctx=ctx
        )
        series_books = result["book_series"]
        if not series_books:
            raise ToolError(f"No series information found for book title '{title}'.")

        current_book_id = _coerce_int((series_books[0].get("book") or {}).get("id"))
        if current_book_id is None:
            raise ToolError(f"No book id found for title '{title}'.")

        parsed = parse_next_in_series(series_books, current_book_id=current_book_id)
        if parsed.next_book is None:
            raise ToolError(
                f"No next book found in the series for book title '{title}'."
            )
        return parsed

    # Attach tool callables for introspection/testing convenience.
    mcp.get_series_by_name = get_series_by_name  # type: ignore[attr-defined]
    mcp.get_series_by_book_title = get_series_by_book_title  # type: ignore[attr-defined]
    mcp.get_next_book_in_series = get_next_book_in_series  # type: ignore[attr-defined]
    mcp.get_next_book_in_series_by_title = get_next_book_in_series_by_title  # type: ignore[attr-defined]

    return mcp
