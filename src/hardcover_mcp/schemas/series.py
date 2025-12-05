from dataclasses import dataclass
from typing import Optional


@dataclass
class SeriesBook:
    position: Optional[int]
    book_id: Optional[int]
    title: str
    release_year: Optional[int]
    rating: Optional[float] = None
    ratings_count: Optional[int] = None


@dataclass
class Series:
    id: Optional[int]
    name: str
    slug: Optional[str]
    books_count: Optional[int]
    books: list[SeriesBook]


@dataclass
class SeriesMembership:
    position: Optional[int]
    series_id: Optional[int]
    series_name: str
    series_slug: Optional[str]
    book_id: Optional[int]
    book_title: str
    book_release_year: Optional[int]


@dataclass
class NextInSeries:
    series_id: Optional[int]
    series_name: str
    series_slug: Optional[str]
    current_position: Optional[int]
    next_book: Optional[SeriesBook]
