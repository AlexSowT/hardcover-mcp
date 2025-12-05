from fastmcp import FastMCP, Context
from fastmcp.exceptions import ToolError
from hardcover_mcp.hardcover_client import HardcoverClient
from hardcover_mcp.queries.user import (
    USER_BOOKS_ALL_QUERY,
    USER_BOOKS_DNF_QUERY,
    USER_BOOKS_READ_QUERY,
    USER_BOOKS_READING_QUERY,
    USER_BOOKS_WANT_TO_READ_QUERY,
    USER_GOALS_QUERY,
    USER_OVERVIEW_QUERY,
)
from hardcover_mcp.schemas.user import UserBook, UserBooks, UserGoal, UserOverview


def _normalize_payload(payload) -> dict:
    """Normalize GraphQL responses that may wrap data or arrive as lists."""
    if isinstance(payload, list):
        payload = payload[0] if payload else {}

    if isinstance(payload, dict) and "data" in payload and isinstance(
        payload["data"], dict
    ):
        payload = payload["data"]

    if not isinstance(payload, dict):
        return {}

    return payload


def _ensure_me(payload) -> dict:
    normalized = _normalize_payload(payload)
    me = normalized.get("me")

    if isinstance(me, list):
        me = me[0] if me else None

    if not isinstance(me, dict) or not me:
        raise ToolError("User information unavailable from API response")

    return me


def _safe_int(value) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _optional_int(value) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_float(value) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def parse_user_overview(payload: dict) -> UserOverview:
    me = _ensure_me(payload)
    return UserOverview(
        want_to_read_count=_safe_int(
            ((me.get("want_to_read_count") or {}).get("aggregate") or {}).get("count")
        ),
        currently_reading_count=_safe_int(
            ((me.get("currently_reading_count") or {}).get("aggregate") or {}).get(
                "count"
            )
        ),
        read_count=_safe_int(
            ((me.get("read_count") or {}).get("aggregate") or {}).get("count")
        ),
        paused_count=_safe_int(
            ((me.get("paused_count") or {}).get("aggregate") or {}).get("count")
        ),
        dnf_count=_safe_int(
            ((me.get("dnf_count") or {}).get("aggregate") or {}).get("count")
        ),
        books_count=_safe_int(me.get("books_count")),
        membership=me.get("membership"),
        membership_ends_at=me.get("membership_ends_at"),
    )


def parse_user_books(payload: dict) -> UserBooks:
    me = _ensure_me(payload)
    books: list[UserBook] = []
    for entry in me.get("user_books", []):
        book_info = (entry or {}).get("book") or {}
        books.append(
            UserBook(
                id=_optional_int(book_info.get("id")),
                title=book_info.get("title", ""),
                first_read_date=entry.get("first_read_date"),
                first_started_reading_date=entry.get("first_started_reading_date"),
                has_review=bool(entry.get("has_review")),
                last_read_date=entry.get("last_read_date"),
                status_id=_optional_int(entry.get("status_id")),
            )
        )

    return UserBooks(books_count=_safe_int(me.get("books_count")), user_books=books)


def parse_user_goals(payload: dict) -> list[UserGoal]:
    me = _ensure_me(payload)
    goals: list[UserGoal] = []
    for goal in me.get("goals", []):
        goals.append(
            UserGoal(
                description=goal.get("description"),
                end_date=goal.get("end_date"),
                completed_at=goal.get("completed_at"),
                goal=_optional_float(goal.get("goal")),
                progress=_optional_float(goal.get("progress")),
                start_date=goal.get("start_date"),
            )
        )

    return goals


def get_users_server(client: HardcoverClient) -> FastMCP:
    """Build a Users server bound to the provided Hardcover client."""
    if client is None:
        raise ToolError("Hardcover client has not been configured")

    mcp = FastMCP(name="UsersMCP")

    async def _query_and_parse_books(query: str, ctx: Context) -> UserBooks:
        result = await client.query(query, ctx=ctx)
        return parse_user_books(result)

    @mcp.tool(
        description="Get the current user's reading stats including shelf counts and membership status.",
        tags={"users", "stats"},
        annotations={"title": "Get user overview", "readOnlyHint": True},
    )
    async def get_user_overview(ctx: Context) -> UserOverview:
        result = await client.query(USER_OVERVIEW_QUERY, ctx=ctx)
        return parse_user_overview(result)

    @mcp.tool(
        description="Get the books the current user is actively reading.",
        tags={"users", "books"},
        annotations={"title": "Get currently reading books", "readOnlyHint": True},
    )
    async def get_user_books_currently_reading(ctx: Context) -> UserBooks:
        return await _query_and_parse_books(USER_BOOKS_READING_QUERY, ctx)

    @mcp.tool(
        description="Get the books the current user has finished reading.",
        tags={"users", "books"},
        annotations={"title": "Get finished books", "readOnlyHint": True},
    )
    async def get_user_books_read(ctx: Context) -> UserBooks:
        return await _query_and_parse_books(USER_BOOKS_READ_QUERY, ctx)

    @mcp.tool(
        description="Get the books the current user did not finish.",
        tags={"users", "books"},
        annotations={"title": "Get DNF books", "readOnlyHint": True},
    )
    async def get_user_books_dnf(ctx: Context) -> UserBooks:
        return await _query_and_parse_books(USER_BOOKS_DNF_QUERY, ctx)

    @mcp.tool(
        description="Get the books the current user wants to read.",
        tags={"users", "books"},
        annotations={"title": "Get want-to-read books", "readOnlyHint": True},
    )
    async def get_user_books_want_to_read(ctx: Context) -> UserBooks:
        return await _query_and_parse_books(USER_BOOKS_WANT_TO_READ_QUERY, ctx)

    @mcp.tool(
        description="Get all books linked to the current user.",
        tags={"users", "books"},
        annotations={"title": "Get all user books", "readOnlyHint": True},
    )
    async def get_user_books_all(ctx: Context) -> UserBooks:
        return await _query_and_parse_books(USER_BOOKS_ALL_QUERY, ctx)

    @mcp.tool(
        description="Get the current user's reading goals and progress.",
        tags={"users", "goals"},
        annotations={"title": "Get user goals", "readOnlyHint": True},
    )
    async def get_user_goals(ctx: Context) -> list[UserGoal]:
        result = await client.query(USER_GOALS_QUERY, ctx=ctx)
        return parse_user_goals(result)

    # Attach tool callables for introspection/testing convenience.
    mcp.get_user_overview = get_user_overview  # type: ignore[attr-defined]
    mcp.get_user_books_currently_reading = get_user_books_currently_reading  # type: ignore[attr-defined]
    mcp.get_user_books_read = get_user_books_read  # type: ignore[attr-defined]
    mcp.get_user_books_dnf = get_user_books_dnf  # type: ignore[attr-defined]
    mcp.get_user_books_want_to_read = get_user_books_want_to_read  # type: ignore[attr-defined]
    mcp.get_user_books_all = get_user_books_all  # type: ignore[attr-defined]
    mcp.get_user_goals = get_user_goals  # type: ignore[attr-defined]

    return mcp
