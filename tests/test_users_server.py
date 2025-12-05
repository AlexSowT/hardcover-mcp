from __future__ import annotations

import asyncio
import sys
import types
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
from hardcover_mcp.server import users as users_module


class DummyContext:
    def __init__(self) -> None:
        self.debug_messages: list[dict] = []

    async def debug(
        self, payload
    ) -> None:  # pragma: no cover - signature defined by fastmcp
        self.debug_messages.append(payload)


@pytest.fixture
def overview_response() -> dict:
    return {
        "me": {
            "want_to_read_count": {"aggregate": {"count": 2}},
            "currently_reading_count": {"aggregate": {"count": 1}},
            "read_count": {"aggregate": {"count": 5}},
            "paused_count": {"aggregate": {"count": 0}},
            "dnf_count": {"aggregate": {"count": 3}},
            "books_count": 11,
            "membership": "pro",
            "membership_ends_at": "2099-01-01",
        }
    }


@pytest.fixture
def overview_response_me_list() -> dict:
    """Matches the real GraphQL shape where `me` is a list."""
    return {
        "me": [
            {
                "want_to_read_count": {"aggregate": {"count": 52}},
                "currently_reading_count": {"aggregate": {"count": 12}},
                "read_count": {"aggregate": {"count": 98}},
                "paused_count": {"aggregate": {"count": 0}},
                "dnf_count": {"aggregate": {"count": 1}},
                "books_count": 110,
                "membership": None,
                "membership_ends_at": None,
            }
        ]
    }


@pytest.fixture
def books_response() -> dict:
    return {
        "me": {
            "books_count": 2,
            "user_books": [
                {
                    "book": {"id": 101, "title": "Example Title"},
                    "first_read_date": "2023-01-01",
                    "first_started_reading_date": "2022-12-30",
                    "has_review": True,
                    "last_read_date": "2023-01-02",
                    "status_id": 2,
                },
                {
                    "book": {"id": None, "title": "Second Book"},
                    "first_read_date": None,
                    "first_started_reading_date": None,
                    "has_review": False,
                    "last_read_date": None,
                    "status_id": None,
                },
            ],
        }
    }


@pytest.fixture
def books_response_me_list(books_response) -> dict:
    """Real responses return `me` as a list; reuse the base fixture for contents."""
    return {"me": [books_response["me"]]}


@pytest.fixture
def goals_response() -> dict:
    return {
        "me": {
            "goals": [
                {
                    "description": "Read 20 books",
                    "end_date": "2024-12-31",
                    "completed_at": None,
                    "goal": "20",
                    "progress": 7,
                    "start_date": "2024-01-01",
                }
            ]
        }
    }


@pytest.fixture
def mock_client(overview_response):
    client = SimpleNamespace()
    client.query = AsyncMock(return_value=overview_response)
    return client


@pytest.fixture
def users_server(mock_client):
    return users_module.get_users_server(mock_client)


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


def test_get_users_server_sets_client_reference(users_server):
    assert hasattr(users_server, "get_user_overview")


def test_parse_user_overview_returns_counts(overview_response):
    overview = users_module.parse_user_overview(overview_response)
    assert isinstance(overview, UserOverview)
    assert overview.want_to_read_count == 2
    assert overview.currently_reading_count == 1
    assert overview.read_count == 5
    assert overview.paused_count == 0
    assert overview.dnf_count == 3
    assert overview.books_count == 11
    assert overview.membership == "pro"
    assert overview.membership_ends_at == "2099-01-01"


def test_parse_user_overview_accepts_wrapped_payload(overview_response):
    wrapped = {"data": overview_response}
    overview = users_module.parse_user_overview(wrapped)
    assert overview.books_count == 11

    list_wrapped = [wrapped]
    overview = users_module.parse_user_overview(list_wrapped)
    assert overview.want_to_read_count == 2


def test_parse_user_overview_handles_me_list_shape(overview_response_me_list):
    overview = users_module.parse_user_overview(overview_response_me_list)
    assert overview.want_to_read_count == 52
    assert overview.currently_reading_count == 12
    assert overview.read_count == 98
    assert overview.paused_count == 0
    assert overview.dnf_count == 1
    assert overview.books_count == 110
    assert overview.membership is None
    assert overview.membership_ends_at is None


def test_parse_user_books_returns_entries(books_response):
    user_books = users_module.parse_user_books(books_response)
    assert isinstance(user_books, UserBooks)
    assert user_books.books_count == 2
    assert len(user_books.user_books) == 2
    first = user_books.user_books[0]
    assert isinstance(first, UserBook)
    assert first.id == 101
    assert first.title == "Example Title"
    assert first.first_read_date == "2023-01-01"
    assert first.first_started_reading_date == "2022-12-30"
    assert first.has_review is True
    assert first.last_read_date == "2023-01-02"
    assert first.status_id == 2
    assert user_books.user_books[1].id is None
    assert user_books.user_books[1].title == "Second Book"
    assert user_books.user_books[1].status_id is None


def test_parse_user_books_accepts_wrapped_payload(books_response):
    wrapped = {"data": books_response}
    user_books = users_module.parse_user_books(wrapped)
    assert user_books.books_count == 2
    assert len(user_books.user_books) == 2

    list_wrapped = [wrapped]
    user_books = users_module.parse_user_books(list_wrapped)
    assert user_books.user_books[0].title == "Example Title"


def test_parse_user_books_handles_me_list_shape(books_response_me_list):
    user_books = users_module.parse_user_books(books_response_me_list)
    assert user_books.books_count == 2


def test_parse_user_goals_returns_entries(goals_response):
    goals = users_module.parse_user_goals(goals_response)
    assert isinstance(goals, list)
    assert len(goals) == 1
    goal = goals[0]
    assert isinstance(goal, UserGoal)
    assert goal.description == "Read 20 books"
    assert goal.end_date == "2024-12-31"
    assert goal.completed_at is None
    assert goal.goal == pytest.approx(20.0)
    assert goal.progress == pytest.approx(7.0)
    assert goal.start_date == "2024-01-01"


def test_get_user_overview_invokes_query(mock_client, users_server):
    ctx = DummyContext()
    overview = invoke_tool(users_server.get_user_overview, ctx)
    mock_client.query.assert_awaited_once_with(USER_OVERVIEW_QUERY, ctx=ctx)
    assert isinstance(overview, UserOverview)


def test_get_user_books_currently_reading_invokes_query(mock_client, users_server):
    ctx = DummyContext()
    invoke_tool(users_server.get_user_books_currently_reading, ctx)
    mock_client.query.assert_awaited_once_with(USER_BOOKS_READING_QUERY, ctx=ctx)


def test_get_user_books_read_invokes_query(mock_client, users_server):
    ctx = DummyContext()
    invoke_tool(users_server.get_user_books_read, ctx)
    mock_client.query.assert_awaited_once_with(USER_BOOKS_READ_QUERY, ctx=ctx)


def test_get_user_books_dnf_invokes_query(mock_client, users_server):
    ctx = DummyContext()
    invoke_tool(users_server.get_user_books_dnf, ctx)
    mock_client.query.assert_awaited_once_with(USER_BOOKS_DNF_QUERY, ctx=ctx)


def test_get_user_books_want_to_read_invokes_query(mock_client, users_server):
    ctx = DummyContext()
    invoke_tool(users_server.get_user_books_want_to_read, ctx)
    mock_client.query.assert_awaited_once_with(USER_BOOKS_WANT_TO_READ_QUERY, ctx=ctx)


def test_get_user_books_all_invokes_query(mock_client, users_server):
    ctx = DummyContext()
    invoke_tool(users_server.get_user_books_all, ctx)
    mock_client.query.assert_awaited_once_with(USER_BOOKS_ALL_QUERY, ctx=ctx)


def test_get_user_goals_invokes_query(mock_client, users_server, goals_response):
    mock_client.query.return_value = goals_response
    ctx = DummyContext()
    invoke_tool(users_server.get_user_goals, ctx)
    mock_client.query.assert_awaited_once_with(USER_GOALS_QUERY, ctx=ctx)
