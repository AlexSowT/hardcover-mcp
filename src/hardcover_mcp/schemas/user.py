from dataclasses import dataclass
from hardcover_mcp.schemas.book import Tagging


@dataclass
class UserOverview:
    want_to_read_count: int
    currently_reading_count: int
    read_count: int
    paused_count: int
    dnf_count: int
    books_count: int
    membership: str | None
    membership_ends_at: str | None


@dataclass
class UserBook:
    id: int | None
    title: str
    first_read_date: str | None
    first_started_reading_date: str | None
    has_review: bool
    last_read_date: str | None
    status_id: int | None
    taggings: list[Tagging] | None = None


@dataclass
class UserBooks:
    books_count: int
    user_books: list[UserBook]


@dataclass
class UserGoal:
    description: str | None
    end_date: str | None
    completed_at: str | None
    goal: float | None
    progress: float | None
    start_date: str | None
