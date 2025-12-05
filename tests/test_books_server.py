from __future__ import annotations

import sys
import types
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

try:  # pragma: no cover - dependency availability varies per environment
    from fastmcp.exceptions import ToolError
except ModuleNotFoundError:  # pragma: no cover - provide a lightweight stub
    fastmcp_module = types.ModuleType("fastmcp")

    class FastMCP:
        def __init__(self, *_, **__):
            pass

        def tool(self, func=None, **__):
            if func is None:
                return lambda wrapped: wrapped
            return func

    class Context:  # matches the attribute the server imports
        pass

    fastmcp_module.FastMCP = FastMCP
    fastmcp_module.Context = Context
    sys.modules["fastmcp"] = fastmcp_module

    fastmcp_exceptions = types.ModuleType("fastmcp.exceptions")

    class ToolError(Exception):
        """Stand-in for fastmcp.exceptions.ToolError used in tests."""

    fastmcp_exceptions.ToolError = ToolError
    sys.modules["fastmcp.exceptions"] = fastmcp_exceptions

    from fastmcp.exceptions import ToolError

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
from hardcover_mcp.schemas.book import Book
from hardcover_mcp.server import books as books_module


BOOK_RESPONSE = {
    "id": 999,
    "title": "Lord Peter Views the Body",
    "release_year": 1928,
    "rating": 3.710526315789474,
    "ratings_count": 19,
    "reviews_count": 3,
    "pages": 320,
    "audio_seconds": 3600,
    "taggings": [
        {"tag": {"tag": "Fantasy", "tag_category": {"id": 1, "category": "Genre"}}},
        {"tag": {"tag": "Fantasy", "tag_category": {"id": 1, "category": "Genre"}}},
    ],
    "contributions": [
        {
            "author": {
                "name": "Dorothy L. Sayers",
            }
        }
    ],
    "description": "Consists of short stories",
    "users_read_count": 24,
}


class DummyContext:
    def __init__(self) -> None:
        self.debug_messages: list[list[Book]] = []

    async def debug(
        self, payload
    ) -> None:  # pragma: no cover - signature defined by fastmcp
        self.debug_messages.append(payload)


@pytest.fixture
def sample_response() -> dict:
    return {"books": [BOOK_RESPONSE]}


@pytest.fixture
def mock_client(sample_response):
    client = SimpleNamespace()
    client.query = AsyncMock(return_value=sample_response)
    return client


@pytest.fixture
def books_server(mock_client):
    return books_module.get_books_server(mock_client)


@pytest.fixture
def reviews_response() -> dict:
    return {
        "user_books": [
            {
                "id": 1,
                "rating": "4.5",
                "review": "Great!",
                "review_has_spoilers": False,
                "created_at": "2024-01-01",
                "user": {"id": 5, "username": "reader"},
            }
        ]
    }


def assert_matches_book(book: Book) -> None:
    assert book.id == BOOK_RESPONSE["id"]
    assert book.title == BOOK_RESPONSE["title"]
    assert book.release_year == BOOK_RESPONSE["release_year"]
    assert book.rating == pytest.approx(float(BOOK_RESPONSE["rating"]))
    assert book.ratings_count == BOOK_RESPONSE["ratings_count"]
    assert book.reviews_count == BOOK_RESPONSE["reviews_count"]
    assert book.author_names == ["Dorothy L. Sayers"]
    assert book.description.startswith("Consists of short stories")
    assert book.users_read_count == BOOK_RESPONSE["users_read_count"]
    assert book.pages == BOOK_RESPONSE["pages"]
    assert book.audio_seconds == BOOK_RESPONSE["audio_seconds"]
    assert len(book.taggings) == 1
    assert book.taggings[0].tag == "Fantasy"


def run_async(coro):
    return asyncio.run(coro)


def unwrap_tool_callable(tool):
    if callable(tool):
        return tool

    for attr in ("fn", "__wrapped__", "callback", "func"):
        candidate = getattr(tool, attr, None)
        if candidate is not None:
            return candidate

    raise TypeError(f"Unsupported tool wrapper type: {type(tool)!r}")


def invoke_tool(tool, *args, **kwargs):
    fn = unwrap_tool_callable(tool)
    return run_async(fn(*args, **kwargs))


def test_get_books_server_sets_client_reference(books_server):
    assert hasattr(books_server, "get_book_by_id")


def test_parse_book_response_accepts_list_payload():
    result = books_module.parse_book_response([BOOK_RESPONSE])
    assert len(result) == 1
    assert_matches_book(result[0])


def test_parse_book_response_accepts_single_dict():
    result = books_module.parse_book_response(BOOK_RESPONSE)
    assert len(result) == 1
    assert_matches_book(result[0])


def test_get_book_by_id_returns_parsed_books(mock_client, books_server):
    ctx = DummyContext()
    result = invoke_tool(books_server.get_book_by_id, 1, ctx)

    mock_client.query.assert_awaited_once_with(
        BOOKS_BY_ID_QUERY,
        variables={"id": 1, "tagging_count_minimum": 5000},
        ctx=ctx,
    )

    assert len(result) == 1
    assert_matches_book(result[0])


def test_get_book_by_id_validates_identifier(mock_client, books_server):
    ctx = DummyContext()
    with pytest.raises(TypeError):
        invoke_tool(books_server.get_book_by_id, 0, ctx)

    assert mock_client.query.await_count == 0


def test_get_books_by_title_returns_parsed_books(mock_client, books_server):
    ctx = DummyContext()
    result = invoke_tool(books_server.get_books_by_title, "anything", ctx)

    mock_client.query.assert_awaited_once_with(
        BOOKS_BY_TITLE_QUERY,
        variables={"title": "anything", "tagging_count_minimum": 5000},
        ctx=ctx,
    )

    assert len(result) == 1
    assert_matches_book(result[0])


def test_get_books_by_title_validates_title(mock_client, books_server):
    with pytest.raises(TypeError):
        invoke_tool(books_server.get_books_by_title, "  ", DummyContext())

    assert mock_client.query.await_count == 0


def test_get_books_by_title_raises_when_no_results(mock_client, books_server):
    mock_client.query.return_value = {"books": []}

    with pytest.raises(ToolError):
        invoke_tool(books_server.get_books_by_title, "missing", DummyContext())


def test_get_books_by_genre_returns_parsed_books(mock_client, books_server):
    ctx = DummyContext()
    result = invoke_tool(
        books_server.get_books_by_genre,
        ["Fantasy"],
        10,
        2,
        1,
        100,
        0,
        9999,
        ctx,
    )

    mock_client.query.assert_awaited_once_with(
        BOOKS_BY_GENRE_QUERY,
        variables={
            "genre": ["Fantasy"],
            "rating_minimum": 10,
            "limit": 2,
            "offset": 1,
            "tagging_count_minimum": 100,
            "min_year": 0,
            "max_year": 9999,
        },
        ctx=ctx,
    )
    assert len(result) == 1
    assert_matches_book(result[0])


@pytest.mark.parametrize(
    "args",
    [
        (["Fantasy"], -1, 1, 0, 0, 0, 9999, DummyContext()),
        (["Fantasy"], 1, 0, 0, 0, 0, 9999, DummyContext()),
        (["Fantasy"], 1, 1, -1, 0, 0, 9999, DummyContext()),
        (["", ""], 1, 1, 0, 0, 0, 9999, DummyContext()),
        (["Fantasy"], 1, 1, 0, 0, -1, 9999, DummyContext()),
        (["Fantasy"], 1, 1, 0, 0, 2025, 2024, DummyContext()),
    ],
)
def test_get_books_by_genre_validates_inputs(mock_client, books_server, args):
    with pytest.raises(TypeError):
        invoke_tool(books_server.get_books_by_genre, *args)
    assert mock_client.query.await_count == 0


@pytest.mark.parametrize(
    "tool_attr, field",
    [
        ("get_books_by_mood", "moods"),
        ("get_books_by_tag", "tags"),
        ("get_books_by_content_warning", "content_warnings"),
        ("get_books_by_pace", "paces"),
    ],
)
def test_book_tag_queries_happy_path(mock_client, books_server, tool_attr, field):
    ctx = DummyContext()
    args = {
        "moods": ["dark"],
        "tags": ["magic"],
        "content_warnings": ["violence"],
        "paces": ["fast"],
    }
    result = invoke_tool(
        getattr(books_server, tool_attr),
        args[field],
        5,
        2,
        0,
        999,
        0,
        9999,
        ctx,
    )
    assert len(result) == 1
    assert_matches_book(result[0])


def test_get_books_by_tag_invokes_query(mock_client):
    books_server = books_module.get_books_server(mock_client)
    ctx = DummyContext()
    invoke_tool(books_server.get_books_by_tag, ["magic"], 5, 1, 0, 50, 0, 9999, ctx)
    mock_client.query.assert_awaited_once_with(
        BOOKS_BY_TAG_QUERY,
        variables={
            "tags": ["magic"],
            "rating_minimum": 5,
            "limit": 1,
            "offset": 0,
            "tagging_count_minimum": 50,
            "min_year": 0,
            "max_year": 9999,
        },
        ctx=ctx,
    )


def test_get_books_by_length_happy_path(mock_client):
    books_server = books_module.get_books_server(mock_client)
    ctx = DummyContext()
    result = invoke_tool(
        books_server.get_books_by_length,
        100,
        300,
        0,
        2,
        0,
        0,
        9999,
        ctx,
    )
    mock_client.query.assert_awaited_once()
    assert len(result) == 1
    assert_matches_book(result[0])


def test_get_books_by_length_validates_bounds(mock_client):
    books_server = books_module.get_books_server(mock_client)
    with pytest.raises(TypeError):
        invoke_tool(
            books_server.get_books_by_length, 300, 100, 0, 1, 0, 0, 9999, DummyContext()
        )
    assert mock_client.query.await_count == 0


def test_get_book_reviews_parses_reviews(mock_client, reviews_response):
    books_server = books_module.get_books_server(mock_client)
    mock_client.query.return_value = reviews_response
    ctx = DummyContext()
    reviews = invoke_tool(books_server.get_book_reviews, 10, 1, 0, ctx)
    mock_client.query.assert_awaited_once_with(
        BOOK_REVIEWS_QUERY,
        variables={"book_id": 10, "limit": 1, "offset": 0},
        ctx=ctx,
    )
    assert len(reviews) == 1
    review = reviews[0]
    assert review.rating == pytest.approx(4.5)
    assert review.username == "reader"


def test_get_book_reviews_validates_inputs(mock_client):
    books_server = books_module.get_books_server(mock_client)
    with pytest.raises(TypeError):
        invoke_tool(books_server.get_book_reviews, 0, 1, 0, DummyContext())
    assert mock_client.query.await_count == 0


def test_get_book_reviews_by_title_happy_path(mock_client, reviews_response):
    books_server = books_module.get_books_server(mock_client)
    mock_client.query.return_value = reviews_response
    ctx = DummyContext()
    reviews = invoke_tool(
        books_server.get_book_reviews_by_title, "Some Title", 1, 0, ctx
    )
    mock_client.query.assert_awaited_once_with(
        BOOK_REVIEWS_BY_TITLE_QUERY,
        variables={"title": "Some Title", "limit": 1, "offset": 0},
        ctx=ctx,
    )
    assert reviews[0].username == "reader"


def test_get_book_reviews_by_title_validates_title(mock_client):
    books_server = books_module.get_books_server(mock_client)
    with pytest.raises(TypeError):
        invoke_tool(books_server.get_book_reviews_by_title, " ", 1, 0, DummyContext())
    assert mock_client.query.await_count == 0
