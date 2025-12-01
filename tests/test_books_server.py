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

from hardcover_mcp.queries.book import BOOKS_BY_ID_QUERY, BOOKS_BY_TITLE_QUERY
from hardcover_mcp.schemas.book import Book
from hardcover_mcp.server import books as books_module


BOOK_RESPONSE = {
    "title": "Lord Peter Views the Body",
    "release_year": 1928,
    "rating": 3.710526315789474,
    "ratings_count": 19,
    "reviews_count": 3,
    "contributions": [
        {
            "author": {
                "name": "Dorothy L. Sayers",
            }
        }
    ],
    "description": (
        "Consists of the following short stories -\r\n"
        "\"The Abominable History of the Man with Copper Fingers\": An artist's jealous "
        "nature leads to an investigation of his mistress' disappearance.\r\n"
        "\"The Entertaining Episode of the Article in Question\": A grammatical mistake "
        "in French unmasks a clever criminal.\r\n"
        "\"The Fascinating Problem of Uncle Meleager's Will\": The disposal of a dead "
        "man's fortune depends on his penchant for cross-word puzzles.\r\n"
        "\"The Fantastic Horror of the Cat in the Bag\": A high-speed chase and a lost "
        "bag converge with a gruesome discovery.\r\n"
        "\"The Unprincipled Affair of the Practical Joker\": A lady pleads for Lord "
        "Peter's help in retrieving a valuable necklace, and more importantly, a "
        "portrait with an indiscreet inscription.\r\n"
        "\"The Undignified Melodrama of the Bone of Contention\": Lord Peter, visiting "
        "friends in the country, sees a ghostly carriage, hears rumors of an odd "
        "will, and deduces that foul play is afoot.\r\n"
        "\"The Vindictive Story of the Footsteps That Ran\": Lord Peter deduces the "
        "whereabouts of a cleverly hidden murder weapon.\r\n"
        "\"The Bibulous Business of a Matter of Taste\": Lord Peter's famous palate is "
        "the deciding factor in acquiring wartime intelligence.\r\n"
        "\"The Learned Adventure of the Dragon's Head\": Viscount St. George appears "
        "as a boy as Lord Peter uses clues from a rare book to find a treasure.\r\n"
        "\"The Piscatorial Farce of the Stolen Stomach\": Involving several Scotsmen, "
        "a digestive organ, and a handful of diamonds.\r\n"
        "\"The Unsolved Puzzle of the Man with No Face\": Which ends with Wimsey "
        "letting a murderer go free, at least partially because he is a good "
        "painter.\r\n"
        "\"The Adventurous Exploit of the Cave of Ali Baba\": Lord Peter infiltrates a "
        "den of ruthless thieves; notable for unusual technology."
    ),
    "users_read_count": 24,
}


class DummyContext:
    def __init__(self) -> None:
        self.debug_messages: list[list[Book]] = []

    async def debug(self, payload) -> None:  # pragma: no cover - signature defined by fastmcp
        self.debug_messages.append(payload)


@pytest.fixture
def sample_response() -> dict:
    """GraphQL payload resembling the Hardcover API response."""

    return {"books": [BOOK_RESPONSE]}


@pytest.fixture
def mock_client(sample_response):
    original_client = books_module._client
    client = SimpleNamespace()
    client.query = AsyncMock(return_value=sample_response)
    books_module._client = client
    yield client
    books_module._client = original_client


def assert_matches_book(book: Book) -> None:
    assert book.title == BOOK_RESPONSE["title"]
    assert book.release_year == BOOK_RESPONSE["release_year"]
    assert book.rating == pytest.approx(float(BOOK_RESPONSE["rating"]))
    assert book.ratings_count == BOOK_RESPONSE["ratings_count"]
    assert book.reviews_count == BOOK_RESPONSE["reviews_count"]
    assert book.author_names == ["Dorothy L. Sayers"]
    assert book.description.startswith("Consists of the following short stories")
    assert book.users_read_count == BOOK_RESPONSE["users_read_count"]


def test_get_books_server_sets_client_reference():
    fake_client = SimpleNamespace()
    original = books_module._client
    try:
        returned = books_module.get_books_server(fake_client)
        assert returned is books_module.mcp
        assert books_module._client is fake_client
    finally:
        books_module._client = original


def test_parse_book_response_accepts_list_payload():
    result = books_module.parse_book_response([BOOK_RESPONSE])
    assert len(result) == 1
    assert_matches_book(result[0])


def test_parse_book_response_accepts_single_dict():
    result = books_module.parse_book_response(BOOK_RESPONSE)
    assert len(result) == 1
    assert_matches_book(result[0])


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


def test_get_book_by_id_returns_parsed_books(mock_client):
    ctx = DummyContext()
    result = invoke_tool(books_module.get_book_by_id, 1, ctx)

    mock_client.query.assert_awaited_once_with(
        BOOKS_BY_ID_QUERY, variables={"id": 1}, ctx=ctx
    )

    assert len(result) == 1
    assert_matches_book(result[0])
    assert ctx.debug_messages == [mock_client.query.return_value]


def test_get_book_by_id_validates_identifier(mock_client):
    ctx = DummyContext()
    with pytest.raises(TypeError):
        invoke_tool(books_module.get_book_by_id, 0, ctx)

    assert mock_client.query.await_count == 0


def test_get_books_by_title_returns_parsed_books(mock_client):
    ctx = DummyContext()
    result = invoke_tool(books_module.get_books_by_title, "anything", ctx)

    mock_client.query.assert_awaited_once_with(
        BOOKS_BY_TITLE_QUERY, variables={"title": "anything"}, ctx=ctx
    )

    assert len(result) == 1
    assert_matches_book(result[0])
    assert ctx.debug_messages == [mock_client.query.return_value]


def test_get_books_by_title_validates_title(mock_client):
    with pytest.raises(TypeError):
        invoke_tool(books_module.get_books_by_title, "  ", DummyContext())

    assert mock_client.query.await_count == 0


def test_get_books_by_title_raises_when_no_results(mock_client):
    mock_client.query.return_value = {"books": []}

    with pytest.raises(ToolError):
        invoke_tool(books_module.get_books_by_title, "missing", DummyContext())
