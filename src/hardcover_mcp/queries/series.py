SERIES_BY_NAME_QUERY = """
    query SeriesByName($name: String!, $limit: Int!, $offset: Int!) {
      series(
        where: {name: {_eq: $name}}
        order_by: {books_count: desc_nulls_last}
        limit: $limit
        offset: $offset
      ) {
        id
        name
        slug
        books_count
        book_series(order_by: {position: asc}) {
          position
          book {
            id
            title
            release_year
            rating
            ratings_count
          }
        }
      }
    }
"""


SERIES_BY_BOOK_TITLE_QUERY = """
    query SeriesByBookTitle($title: String!, $limit: Int!) {
      book_series(
        where: {book: {title: {_eq: $title}}}
        order_by: {position: asc}
        limit: $limit
      ) {
        position
        series {
          id
          name
          slug
        }
        book {
          id
          title
          release_year
        }
      }
    }
"""


SERIES_NEXT_BOOK_QUERY = """
    query SeriesOrderForBook($book_id: Int!) {
      book_series(where: {book_id: {_eq: $book_id}}, limit: 1) {
        position
        series {
          id
          name
          slug
          book_series(order_by: {position: asc}) {
            position
            book {
              id
              title
              release_year
            }
          }
        }
      }
    }
"""


SERIES_NEXT_BOOK_BY_TITLE_QUERY = """
    query SeriesOrderForBookTitle($title: String!) {
      book_series(where: {book: {title: {_eq: $title}}}, limit: 1) {
        position
        book { id title release_year }
        series {
          id
          name
          slug
          book_series(order_by: {position: asc}) {
            position
            book {
              id
              title
              release_year
            }
          }
        }
      }
    }
"""
