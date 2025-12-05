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

from hardcover_mcp.schemas.series import Series, SeriesMembership, NextInSeries
from hardcover_mcp.queries.series import (
    SERIES_BY_NAME_QUERY,
    SERIES_BY_BOOK_TITLE_QUERY,
    SERIES_NEXT_BOOK_QUERY,
    SERIES_NEXT_BOOK_BY_TITLE_QUERY,
)
from hardcover_mcp.server import series as series_module


SERIES_RESPONSE = {
    "series": [
        {
            "id": 1,
            "name": "Mistborn",
            "slug": "mistborn",
            "books_count": 3,
            "book_series": [
                {
                    "position": 1,
                    "book": {
                        "id": 101,
                        "title": "Final Empire",
                        "release_year": 2006,
                        "rating": 4.5,
                        "ratings_count": 1000,
                    },
                },
                {
                    "position": 2,
                    "book": {
                        "id": 102,
                        "title": "Well of Ascension",
                        "release_year": 2007,
                        "rating": 4.4,
                        "ratings_count": 900,
                    },
                },
            ],
        }
    ]
}

SERIES_BY_BOOK_TITLE_RESPONSE = {
    "book_series": [
        {
            "position": 2,
            "series": {"id": 1, "name": "Mistborn", "slug": "mistborn"},
            "book": {"id": 102, "title": "Well of Ascension", "release_year": 2007},
        }
    ]
}

SERIES_NEXT_RESPONSE = {
    "book_series": [
        {
            "position": 2,
            "series": {
                "id": 1,
                "name": "Mistborn",
                "slug": "mistborn",
                "book_series": [
                    {
                        "position": 1,
                        "book": {
                            "id": 101,
                            "title": "Final Empire",
                            "release_year": 2006,
                        },
                    },
                    {
                        "position": 2,
                        "book": {
                            "id": 102,
                            "title": "Well of Ascension",
                            "release_year": 2007,
                        },
                    },
                    {
                        "position": 3,
                        "book": {
                            "id": 103,
                            "title": "Hero of Ages",
                            "release_year": 2008,
                        },
                    },
                ],
            },
        }
    ]
}

SERIES_NEXT_BY_TITLE_RESPONSE = {
    "book_series": [
        {
            "position": 2,
            "book": {"id": 102, "title": "Well of Ascension", "release_year": 2007},
            "series": {
                "id": 1,
                "name": "Mistborn",
                "slug": "mistborn",
                "book_series": [
                    {
                        "position": 1,
                        "book": {
                            "id": 101,
                            "title": "Final Empire",
                            "release_year": 2006,
                        },
                    },
                    {
                        "position": 2,
                        "book": {
                            "id": 102,
                            "title": "Well of Ascension",
                            "release_year": 2007,
                        },
                    },
                    {
                        "position": 3,
                        "book": {
                            "id": 103,
                            "title": "Hero of Ages",
                            "release_year": 2008,
                        },
                    },
                ],
            },
        }
    ]
}


class DummyContext:
    def __init__(self) -> None:
        self.debug_messages: list[list[Series]] = []

    async def debug(self, payload) -> None:  # pragma: no cover
        self.debug_messages.append(payload)


@pytest.fixture
def mock_client():
    client = SimpleNamespace()
    client.query = AsyncMock(return_value=SERIES_RESPONSE)
    return client


@pytest.fixture
def series_server(mock_client):
    return series_module.get_series_server(mock_client)


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


def test_get_series_by_name_returns_series(mock_client, series_server):
    ctx = DummyContext()
    result = invoke_tool(series_server.get_series_by_name, "mistborn", ctx, 1, 0)
    mock_client.query.assert_awaited_once_with(
        SERIES_BY_NAME_QUERY,
        variables={"name": "mistborn", "limit": 1, "offset": 0},
        ctx=ctx,
    )
    assert isinstance(result[0], Series)
    assert result[0].name == "Mistborn"
    assert result[0].books[0].title == "Final Empire"


def test_get_series_by_name_validates_name(mock_client, series_server):
    with pytest.raises(TypeError):
        invoke_tool(series_server.get_series_by_name, "   ", DummyContext(), 1, 0)
    assert mock_client.query.await_count == 0


def test_get_series_by_book_title_returns_memberships(mock_client, series_server):
    mock_client.query.return_value = SERIES_BY_BOOK_TITLE_RESPONSE
    ctx = DummyContext()
    memberships = invoke_tool(
        series_server.get_series_by_book_title, "Well of Ascension", ctx, 3
    )
    mock_client.query.assert_awaited_once_with(
        SERIES_BY_BOOK_TITLE_QUERY,
        variables={"title": "Well of Ascension", "limit": 3},
        ctx=ctx,
    )
    assert isinstance(memberships[0], SeriesMembership)
    assert memberships[0].series_name == "Mistborn"


def test_get_next_book_in_series_returns_next(mock_client, series_server):
    mock_client.query.return_value = SERIES_NEXT_RESPONSE
    ctx = DummyContext()
    next_book = invoke_tool(series_server.get_next_book_in_series, 102, ctx)
    mock_client.query.assert_awaited_once_with(
        SERIES_NEXT_BOOK_QUERY,
        variables={"book_id": 102},
        ctx=ctx,
    )
    assert isinstance(next_book, NextInSeries)
    assert next_book.next_book.title == "Hero of Ages"


def test_get_next_book_in_series_by_title_returns_next(
    mock_client, series_server
):
    mock_client.query.return_value = SERIES_NEXT_BY_TITLE_RESPONSE
    ctx = DummyContext()
    next_book = invoke_tool(
        series_server.get_next_book_in_series_by_title, "Well of Ascension", ctx
    )
    mock_client.query.assert_awaited_once_with(
        SERIES_NEXT_BOOK_BY_TITLE_QUERY,
        variables={"title": "Well of Ascension"},
        ctx=ctx,
    )
    assert isinstance(next_book, NextInSeries)
    assert next_book.next_book.title == "Hero of Ages"


def test_get_next_book_in_series_validates_input(mock_client, series_server):
    with pytest.raises(TypeError):
        invoke_tool(series_server.get_next_book_in_series, 0, DummyContext())
    assert mock_client.query.await_count == 0


def test_get_next_book_in_series_by_title_validates_input(mock_client, series_server):
    with pytest.raises(TypeError):
        invoke_tool(
            series_server.get_next_book_in_series_by_title, "  ", DummyContext()
        )
    assert mock_client.query.await_count == 0
