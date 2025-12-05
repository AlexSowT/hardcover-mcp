from fastmcp import FastMCP, Context
from fastmcp.exceptions import ToolError
from hardcover_mcp.hardcover_client import HardcoverClient
from hardcover_mcp.schemas.book import Book, BookReview, Tagging
from hardcover_mcp.queries.book import (
    BOOKS_BY_ID_QUERY,
    BOOKS_BY_TITLE_QUERY,
    BOOKS_BY_GENRE_QUERY,
    BOOKS_BY_MOOD_QUERY,
    BOOKS_BY_TAG_QUERY,
    BOOKS_BY_CONTENT_WARNING_QUERY,
    BOOKS_BY_PACE_QUERY,
    BOOKS_BY_LENGTH_QUERY,
    BOOK_REVIEWS_QUERY,
    BOOK_REVIEWS_BY_TITLE_QUERY,
)


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


def _validate_str_list(values: list[str], field: str) -> list[str]:
    if not isinstance(values, list) or not values:
        raise TypeError(f"{field} must be a non-empty list of strings")
    cleaned: list[str] = []
    for item in values:
        if not isinstance(item, str) or not item.strip():
            raise TypeError(f"Every entry in {field} must be a non-empty string")
        cleaned.append(item.strip())
    return cleaned


def _validate_paging(limit: int, offset: int = 0) -> None:
    if not isinstance(limit, int) or limit < 1 or limit > 50:
        raise TypeError("limit must be an integer between 1 and 50")
    if not isinstance(offset, int) or offset < 0:
        raise TypeError("offset must be a non-negative integer")


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

        pages = book.get("pages")
        try:
            pages = int(pages) if pages is not None else None
        except (TypeError, ValueError):
            pages = None

        audio_seconds = book.get("audio_seconds")
        try:
            audio_seconds = int(audio_seconds) if audio_seconds is not None else None
        except (TypeError, ValueError):
            audio_seconds = None

        taggings: list[Tagging] = []
        seen = set()
        for tagging in book.get("taggings", []) or []:
            tag_info = tagging.get("tag") if tagging else {}
            tag_value = tag_info.get("tag", "")
            cat = (tag_info.get("tag_category") or {}).get("category")
            cat_id = (tag_info.get("tag_category") or {}).get("id")
            dedup_key = (tag_value, cat_id)
            if dedup_key in seen:
                continue
            seen.add(dedup_key)
            taggings.append(
                Tagging(
                    tag=tag_value,
                    category=cat,
                    category_id=cat_id,
                )
            )

        parsed.append(
            Book(
                id=_coerce_int(book.get("id")),
                title=book.get("title", ""),
                release_year=book.get("release_year"),
                rating=rating,
                ratings_count=book.get("ratings_count", 0),
                reviews_count=book.get("reviews_count", 0),
                author_names=author_names,
                description=book.get("description", ""),
                users_read_count=book.get("users_read_count", 0),
                pages=pages,
                audio_seconds=audio_seconds,
                taggings=taggings,
            )
        )

    return parsed


def parse_book_reviews(reviews_data) -> list[BookReview]:
    parsed: list[BookReview] = []
    for entry in reviews_data:
        user = (entry or {}).get("user") or {}
        rating = entry.get("rating")
        try:
            rating = float(rating) if rating is not None else None
        except (TypeError, ValueError):
            rating = None

        parsed.append(
            BookReview(
                id=entry.get("id"),
                rating=rating,
                review=entry.get("review", ""),
                review_has_spoilers=bool(entry.get("review_has_spoilers")),
                created_at=entry.get("created_at"),
                user_id=user.get("id"),
                username=user.get("username"),
            )
        )
    return parsed


def get_books_server(client: HardcoverClient) -> FastMCP:
    """Build a Books server bound to the provided Hardcover client."""
    if client is None:
        raise ToolError("Hardcover client has not been configured")

    mcp = FastMCP(name="BooksMCP")

    @mcp.tool(
        description="""Search the Hardcover database to get a book by hardcover book ID. 
                        Returns infomation such as name, author, descirpitob, reviews, and the mood and genre of the book.
                        Important: This tool should only be used with a Hardcover ID.""",
        tags={"books", "search"},
        annotations={"title": "Search books by Title", "readOnlyHint": True},
    )
    async def get_book_by_id(
        id: int, ctx: Context, tagging_count_minimum: int = 5000
    ) -> list[Book]:
        if not isinstance(id, int) or id < 1:
            raise TypeError(f"Book ID must be a positive integer. id: {id}")
        if not isinstance(tagging_count_minimum, int) or tagging_count_minimum < 0:
            raise TypeError("tagging_count_minimum must be a non-negative integer")

        result = await client.query(
            BOOKS_BY_ID_QUERY,
            variables={"id": id, "tagging_count_minimum": tagging_count_minimum},
            ctx=ctx,
        )
        book_data = result["books"]

        return parse_book_response(book_data)

    @mcp.tool(
        description="""Search the Hardcover database to get a book by the provided name. 
                        Returns infomation such as name, author, descirpitob, reviews, and the mood and genre of the book""",
        tags={"books", "search"},
        annotations={"title": "Search books by Title", "readOnlyHint": True},
    )
    async def get_books_by_title(
        title: str, ctx: Context, tagging_count_minimum: int = 5000
    ) -> list[Book]:
        if not isinstance(title, str) or not title.strip():
            raise TypeError("Title must be a non-empty string")

        result = await client.query(
            BOOKS_BY_TITLE_QUERY,
            variables={"title": title, "tagging_count_minimum": tagging_count_minimum},
            ctx=ctx,
        )
        book_data = result["books"]

        if len(book_data) == 0:
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
        min_year: int = 0,
        max_year: int = 9999,
        ctx: Context | None = None,
    ) -> list[Book]:
        genres = _validate_str_list(genre, "genre")
        if rating_minimum < 0:
            raise TypeError("rating_minimum must be a non-negative integer")
        _validate_paging(limit, offset)
        if min_year < 0 or max_year < min_year:
            raise TypeError("Year range must be valid and non-negative")

        result = await client.query(
            BOOKS_BY_GENRE_QUERY,
            variables={
                "genre": genres,
                "rating_minimum": rating_minimum,
                "limit": limit,
                "offset": offset,
                "tagging_count_minimum": tagging_count_minimum,
                "min_year": min_year,
                "max_year": max_year,
            },
            ctx=ctx,
        )
        book_data = result["books"]

        if len(book_data) == 0:
            raise ToolError(
                f"No books found with the genre {genre} that had over {rating_minimum} ratings."
            )

        return parse_book_response(book_data)

    @mcp.tool(
        description="Search books by mood tags.",
        tags={"books", "search"},
        annotations={"title": "Search books by Mood", "readOnlyHint": True},
    )
    async def get_books_by_mood(
        moods: list[str],
        rating_minimum: int = 50,
        limit: int = 5,
        offset: int = 0,
        tagging_count_minimum: int = 5000,
        min_year: int = 0,
        max_year: int = 9999,
        ctx: Context | None = None,
    ) -> list[Book]:
        mood_list = [m.lower() for m in _validate_str_list(moods, "moods")]
        if rating_minimum < 0:
            raise TypeError("rating_minimum must be a non-negative integer")
        _validate_paging(limit, offset)
        if min_year < 0 or max_year < min_year:
            raise TypeError("Year range must be valid and non-negative")

        result = await client.query(
            BOOKS_BY_MOOD_QUERY,
            variables={
                "moods": mood_list,
                "rating_minimum": rating_minimum,
                "limit": limit,
                "offset": offset,
                "tagging_count_minimum": tagging_count_minimum,
                "min_year": min_year,
                "max_year": max_year,
            },
            ctx=ctx,
        )
        books = result["books"]
        if not books:
            raise ToolError(
                f"No books found with moods {moods} that had over {rating_minimum} ratings."
            )
        return parse_book_response(books)

    @mcp.tool(
        description="Search books by general tags.",
        tags={"books", "search"},
        annotations={"title": "Search books by Tag", "readOnlyHint": True},
    )
    async def get_books_by_tag(
        tags: list[str],
        rating_minimum: int = 50,
        limit: int = 5,
        offset: int = 0,
        tagging_count_minimum: int = 5000,
        min_year: int = 0,
        max_year: int = 9999,
        ctx: Context | None = None,
    ) -> list[Book]:
        tag_list = [t.lower() for t in _validate_str_list(tags, "tags")]
        if rating_minimum < 0:
            raise TypeError("rating_minimum must be a non-negative integer")
        _validate_paging(limit, offset)
        if min_year < 0 or max_year < min_year:
            raise TypeError("Year range must be valid and non-negative")

        result = await client.query(
            BOOKS_BY_TAG_QUERY,
            variables={
                "tags": tag_list,
                "rating_minimum": rating_minimum,
                "limit": limit,
                "offset": offset,
                "tagging_count_minimum": tagging_count_minimum,
                "min_year": min_year,
                "max_year": max_year,
            },
            ctx=ctx,
        )
        books = result["books"]
        if not books:
            raise ToolError(
                f"No books found with tags {tags} that had over {rating_minimum} ratings."
            )
        return parse_book_response(books)

    @mcp.tool(
        description="Search books by content warnings.",
        tags={"books", "search"},
        annotations={"title": "Search books by Content Warning", "readOnlyHint": True},
    )
    async def get_books_by_content_warning(
        content_warnings: list[str],
        rating_minimum: int = 50,
        limit: int = 5,
        offset: int = 0,
        tagging_count_minimum: int = 5000,
        min_year: int = 0,
        max_year: int = 9999,
        ctx: Context | None = None,
    ) -> list[Book]:
        warnings_list = _validate_str_list(content_warnings, "content_warnings")
        if rating_minimum < 0:
            raise TypeError("rating_minimum must be a non-negative integer")
        _validate_paging(limit, offset)
        if min_year < 0 or max_year < min_year:
            raise TypeError("Year range must be valid and non-negative")

        result = await client.query(
            BOOKS_BY_CONTENT_WARNING_QUERY,
            variables={
                "content_warnings": warnings_list,
                "rating_minimum": rating_minimum,
                "limit": limit,
                "offset": offset,
                "tagging_count_minimum": tagging_count_minimum,
                "min_year": min_year,
                "max_year": max_year,
            },
            ctx=ctx,
        )
        books = result["books"]
        if not books:
            raise ToolError(
                f"No books found with content warnings {content_warnings} that had over {rating_minimum} ratings."
            )
        return parse_book_response(books)

    @mcp.tool(
        description="Search books by pace tags.",
        tags={"books", "search"},
        annotations={"title": "Search books by Pace", "readOnlyHint": True},
    )
    async def get_books_by_pace(
        paces: list[str],
        rating_minimum: int = 50,
        limit: int = 5,
        offset: int = 0,
        tagging_count_minimum: int = 5000,
        min_year: int = 0,
        max_year: int = 9999,
        ctx: Context | None = None,
    ) -> list[Book]:
        pace_list = _validate_str_list(paces, "paces")
        if rating_minimum < 0:
            raise TypeError("rating_minimum must be a non-negative integer")
        _validate_paging(limit, offset)
        if min_year < 0 or max_year < min_year:
            raise TypeError("Year range must be valid and non-negative")

        result = await client.query(
            BOOKS_BY_PACE_QUERY,
            variables={
                "paces": pace_list,
                "rating_minimum": rating_minimum,
                "limit": limit,
                "offset": offset,
                "tagging_count_minimum": tagging_count_minimum,
                "min_year": min_year,
                "max_year": max_year,
            },
            ctx=ctx,
        )
        books = result["books"]
        if not books:
            raise ToolError(
                f"No books found with paces {paces} that had over {rating_minimum} ratings."
            )
        return parse_book_response(books)

    @mcp.tool(
        description="Search books by length (pages).",
        tags={"books", "search"},
        annotations={"title": "Search books by Length", "readOnlyHint": True},
    )
    async def get_books_by_length(
        min_pages: int,
        max_pages: int | None = None,
        rating_minimum: int = 0,
        limit: int = 5,
        offset: int = 0,
        min_year: int = 0,
        max_year: int = 9999,
        ctx: Context | None = None,
    ) -> list[Book]:
        if not isinstance(min_pages, int) or min_pages < 0:
            raise TypeError("min_pages must be a non-negative integer")
        if max_pages is not None:
            if not isinstance(max_pages, int) or max_pages < min_pages:
                raise TypeError(
                    "max_pages must be an integer greater than or equal to min_pages"
                )
        if rating_minimum < 0:
            raise TypeError("rating_minimum must be a non-negative integer")
        _validate_paging(limit, offset)
        if min_year < 0 or max_year < min_year:
            raise TypeError("Year range must be valid and non-negative")

        upper = max_pages if max_pages is not None else 1_000_000

        result = await client.query(
            BOOKS_BY_LENGTH_QUERY,
            variables={
                "min_pages": min_pages,
                "max_pages": upper,
                "rating_minimum": rating_minimum,
                "limit": limit,
                "offset": offset,
                "min_year": min_year,
                "max_year": max_year,
            },
            ctx=ctx,
        )
        books = result["books"]
        if not books:
            raise ToolError(
                f"No books found with page length between {min_pages} and {upper} and at least {rating_minimum} ratings."
            )
        return parse_book_response(books)

    @mcp.tool(
        description="Get reviews for a book by Hardcover book ID.",
        tags={"books", "reviews"},
        annotations={"title": "Get book reviews", "readOnlyHint": True},
    )
    async def get_book_reviews(
        book_id: int,
        limit: int = 10,
        offset: int = 0,
        ctx: Context | None = None,
    ) -> list[BookReview]:
        if not isinstance(book_id, int) or book_id < 1:
            raise TypeError("book_id must be a positive integer")
        _validate_paging(limit, offset)

        result = await client.query(
            BOOK_REVIEWS_QUERY,
            variables={"book_id": book_id, "limit": limit, "offset": offset},
            ctx=ctx,
        )
        reviews = result["user_books"]
        if not reviews:
            raise ToolError(f"No reviews found for book id {book_id}.")
        return parse_book_reviews(reviews)

    @mcp.tool(
        description="Get reviews for a book by title.",
        tags={"books", "reviews"},
        annotations={"title": "Get book reviews by title", "readOnlyHint": True},
    )
    async def get_book_reviews_by_title(
        title: str,
        limit: int = 10,
        offset: int = 0,
        ctx: Context | None = None,
    ) -> list[BookReview]:
        if not isinstance(title, str) or not title.strip():
            raise TypeError("title must be a non-empty string")
        _validate_paging(limit, offset)

        result = await client.query(
            BOOK_REVIEWS_BY_TITLE_QUERY,
            variables={"title": title.strip(), "limit": limit, "offset": offset},
            ctx=ctx,
        )
        reviews = result["user_books"]
        if not reviews:
            raise ToolError(f"No reviews found for book title {title}.")
        return parse_book_reviews(reviews)

    # Attach tool callables for introspection/testing convenience.
    mcp.get_book_by_id = get_book_by_id  # type: ignore[attr-defined]
    mcp.get_books_by_title = get_books_by_title  # type: ignore[attr-defined]
    mcp.get_books_by_genre = get_books_by_genre  # type: ignore[attr-defined]
    mcp.get_books_by_mood = get_books_by_mood  # type: ignore[attr-defined]
    mcp.get_books_by_tag = get_books_by_tag  # type: ignore[attr-defined]
    mcp.get_books_by_content_warning = get_books_by_content_warning  # type: ignore[attr-defined]
    mcp.get_books_by_pace = get_books_by_pace  # type: ignore[attr-defined]
    mcp.get_books_by_length = get_books_by_length  # type: ignore[attr-defined]
    mcp.get_book_reviews = get_book_reviews  # type: ignore[attr-defined]
    mcp.get_book_reviews_by_title = get_book_reviews_by_title  # type: ignore[attr-defined]

    return mcp
