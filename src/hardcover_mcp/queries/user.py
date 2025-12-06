USER_OVERVIEW_QUERY = """
    query GetUserOverview {
      me {
        want_to_read_count: user_books_aggregate(where: {status_id: {_eq: 1}}) {
          aggregate {
            count
          }
        }
        currently_reading_count: user_books_aggregate(
          where: {status_id: {_eq: 2}}
        ) {
          aggregate {
            count
          }
        }
        read_count: user_books_aggregate(where: {status_id: {_eq: 3}}) {
          aggregate {
            count
          }
        }
        paused_count: user_books_aggregate(where: {status_id: {_eq: 4}}) {
          aggregate {
            count
          }
        }
        dnf_count: user_books_aggregate(where: {status_id: {_eq: 5}}) {
          aggregate {
            count
          }
        }
        books_count
        membership
        membership_ends_at
      }
    }
"""


USER_BOOK_FIELDS_FRAGMENT = """
        book {
          id
          title
          taggings(
            where: {tag: {count: {_gt: 5000}}}
            order_by: {tag: {tag_category: {id: asc}, count: desc}}
            limit: 25
          ) {
            tag { tag tag_category { id category } }
          }
        }
        first_read_date
        first_started_reading_date
        has_review
        last_read_date
        status_id
"""


USER_BOOKS_READING_QUERY = f"""
    query GetUserBooksReading {{
      me {{
        books_count
        user_books(where: {{ status_id: {{ _eq: 2 }} }}) {{
{USER_BOOK_FIELDS_FRAGMENT}
        }}
      }}
    }}
"""

USER_BOOKS_READ_QUERY = f"""
    query GetUserBooksRead {{
      me {{
        books_count
        user_books(where: {{ status_id: {{ _eq: 3 }} }}) {{
{USER_BOOK_FIELDS_FRAGMENT}
        }}
      }}
    }}
"""

USER_BOOKS_DNF_QUERY = f"""
    query GetUserBooksDNF {{
      me {{
        books_count
        user_books(where: {{ status_id: {{ _eq: 5 }} }}) {{
{USER_BOOK_FIELDS_FRAGMENT}
        }}
      }}
    }}
"""

USER_BOOKS_WANT_TO_READ_QUERY = f"""
    query GetUserBooksWantToRead {{
      me {{
        books_count
        user_books(where: {{ status_id: {{ _eq: 1 }} }}) {{
{USER_BOOK_FIELDS_FRAGMENT}
        }}
      }}
    }}
"""

USER_BOOKS_ALL_QUERY = f"""
    query GetUserBooksAll {{
      me {{
        books_count
        user_books {{
{USER_BOOK_FIELDS_FRAGMENT}
        }}
      }}
    }}
"""


USER_GOALS_QUERY = """
    query GetUserGoals {
      me {
        goals {
          description
          end_date
          completed_at
          goal
          progress
          start_date
        }
      }
    }
"""
