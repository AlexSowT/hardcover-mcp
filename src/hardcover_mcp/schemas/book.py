from dataclasses import dataclass


@dataclass
class Book:
    title: str
    ratings_count: int
    reviews_count: int
    users_read_count: int
    author_names: list[str]
    release_year: int | None
    rating: float | None
    description: str | None
