from dataclasses import dataclass


@dataclass
class Book:
    id: int | None
    title: str
    ratings_count: int
    reviews_count: int
    users_read_count: int
    author_names: list[str]
    release_year: int | None
    rating: float | None
    description: str | None
    pages: int | None = None
    audio_seconds: int | None = None
    taggings: list["Tagging"] | None = None


@dataclass
class BookReview:
    id: int | None
    rating: float | None
    review: str
    review_has_spoilers: bool
    created_at: str | None
    user_id: int | None
    username: str | None


@dataclass
class Tagging:
    tag: str
    category: str | None
    category_id: int | None
