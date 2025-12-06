BOOKS_BY_ID_QUERY = """
    query BookByID($id: Int!, $tagging_count_minimum: Int = 0) {
      books(where: {id: {_eq: $id}}, limit: 1) {
        id
        title
        subtitle
        release_year
        rating
        ratings_count
        reviews_count
        users_read_count
        pages
        audio_seconds
        description
        contributions {
          author { name }
        }
        taggings(
          where: {tag: {count: {_gt: $tagging_count_minimum}}}
          order_by: {tag: {tag_category: {id: asc}, count: desc}}
          limit: 25
        ) {
          tag { tag tag_category { id category } }
        }
      }
    }
"""


BOOKS_BY_TITLE_QUERY = """
    query BookByTitle($title: String!, $tagging_count_minimum: Int!) {
      books(where: {title: {_eq: $title}}) {
        id
        title
        release_year
        rating
        ratings_count
        reviews_count
        users_read_count
        description
        contributions {
          author { name }
        }
        taggings(
          where: {tag: {count: {_gt: $tagging_count_minimum}}}
          order_by: {tag: {tag_category: {id: asc}, count: desc}}
          limit: 25
        ) {
          tag { tag tag_category { id category } }
        }
      }
    }
"""


BOOKS_BY_GENRE_QUERY = """
    query BooksByGenre(
      $genre: [String!]
      $rating_minimum: Int!
      $tagging_count_minimum: Int!
      $limit: Int!
      $offset: Int!
      $min_year: Int!
      $max_year: Int!
    ) {
      books(
        where: {
          _and: [
            {ratings_count: {_gte: $rating_minimum}},
            {taggings: {tag: {tag: {_in: $genre}, tag_category: {id: {_eq: 1}}}}},
            {release_year: {_gte: $min_year}},
            {release_year: {_lte: $max_year}}
          ]
        }
        order_by: [{rating: desc_nulls_last}, {ratings_count: desc_nulls_last}]
        limit: $limit
        offset: $offset
      ) {
        title
        release_year
        rating
        ratings_count
        reviews_count
        users_read_count
        description
        contributions { author { name } }
        taggings(where: {tag: {count: {_gt: $tagging_count_minimum}}}) {
          tag { tag tag_category { id category } }
        }
      }
    }
"""


BOOKS_BY_MOOD_QUERY = """
    query BooksByMood(
      $moods: [String!]
      $rating_minimum: Int!
      $tagging_count_minimum: Int!
      $limit: Int!
      $offset: Int!
      $min_year: Int!
      $max_year: Int!
    ) {
      books(
        where: {
          _and: [
            {ratings_count: {_gte: $rating_minimum}},
            {taggings: {tag: {tag: {_in: $moods}, tag_category: {id: {_eq: 4}}}}},
            {release_year: {_gte: $min_year}},
            {release_year: {_lte: $max_year}}
          ]
        }
        order_by: [{rating: desc_nulls_last}, {ratings_count: desc_nulls_last}]
        limit: $limit
        offset: $offset
      ) {
        title
        release_year
        rating
        ratings_count
        reviews_count
        users_read_count
        description
        contributions { author { name } }
        taggings(where: {tag: {count: {_gt: $tagging_count_minimum}}}) {
          tag { tag tag_category { id category } }
        }
      }
    }
"""


BOOKS_BY_TAG_QUERY = """
    query BooksByTag(
      $tags: [String!]
      $rating_minimum: Int!
      $tagging_count_minimum: Int!
      $limit: Int!
      $offset: Int!
      $min_year: Int!
      $max_year: Int!
    ) {
      books(
        where: {
          _and: [
            {ratings_count: {_gte: $rating_minimum}},
            {taggings: {tag: {tag: {_in: $tags}}}},
            {release_year: {_gte: $min_year}},
            {release_year: {_lte: $max_year}}
          ]
        }
        order_by: [{rating: desc_nulls_last}, {ratings_count: desc_nulls_last}]
        limit: $limit
        offset: $offset
      ) {
        title
        release_year
        rating
        ratings_count
        reviews_count
        users_read_count
        description
        contributions { author { name } }
        taggings(where: {tag: {count: {_gt: $tagging_count_minimum}}}) {
          tag { tag tag_category { id category } }
        }
      }
    }
"""


BOOKS_BY_CONTENT_WARNING_QUERY = """
    query BooksByContentWarning(
      $content_warnings: [String!]
      $rating_minimum: Int!
      $tagging_count_minimum: Int!
      $limit: Int!
      $offset: Int!
      $min_year: Int!
      $max_year: Int!
    ) {
      books(
        where: {
          _and: [
            {ratings_count: {_gte: $rating_minimum}},
            {taggings: {tag: {tag: {_in: $content_warnings}, tag_category: {id: {_eq: 3}}}}},
            {release_year: {_gte: $min_year}},
            {release_year: {_lte: $max_year}}
          ]
        }
        order_by: [{rating: desc_nulls_last}, {ratings_count: desc_nulls_last}]
        limit: $limit
        offset: $offset
      ) {
        title
        release_year
        rating
        ratings_count
        reviews_count
        users_read_count
        description
        contributions { author { name } }
        taggings(where: {tag: {count: {_gt: $tagging_count_minimum}}}) {
          tag { tag tag_category { id category } }
        }
      }
    }
"""


BOOKS_BY_PACE_QUERY = """
    query BooksByPace(
      $paces: [String!]
      $rating_minimum: Int!
      $tagging_count_minimum: Int!
      $limit: Int!
      $offset: Int!
      $min_year: Int!
      $max_year: Int!
    ) {
      books(
        where: {
          _and: [
            {ratings_count: {_gte: $rating_minimum}},
            {taggings: {tag: {tag: {_in: $paces}, tag_category: {id: {_eq: 37}}}}},
            {release_year: {_gte: $min_year}},
            {release_year: {_lte: $max_year}}
          ]
        }
        order_by: [{rating: desc_nulls_last}, {ratings_count: desc_nulls_last}]
        limit: $limit
        offset: $offset
      ) {
        title
        release_year
        rating
        ratings_count
        reviews_count
        users_read_count
        description
        contributions { author { name } }
        taggings(where: {tag: {count: {_gt: $tagging_count_minimum}}}) {
          tag { tag tag_category { id category } }
        }
      }
    }
"""


BOOKS_BY_LENGTH_QUERY = """
    query BooksByLength(
      $min_pages: Int!
      $max_pages: Int = 1000000
      $rating_minimum: Int!
      $limit: Int!
      $offset: Int!
      $min_year: Int!
      $max_year: Int!
    ) {
      books(
        where: {
          _and: [
            {ratings_count: {_gte: $rating_minimum}},
            {pages: {_gte: $min_pages}},
            {pages: {_lte: $max_pages}},
            {release_year: {_gte: $min_year}},
            {release_year: {_lte: $max_year}}
          ]
        }
        order_by: {pages: asc_nulls_last}
        limit: $limit
        offset: $offset
      ) {
        id
        title
        pages
        audio_seconds
        release_year
        rating
        ratings_count
        reviews_count
        users_read_count
        description
        contributions { author { name } }
        taggings(where: {tag: {count: {_gt: 0}}}) {
          tag { tag tag_category { id category } }
        }
      }
    }
"""


BOOK_REVIEWS_BY_TITLE_QUERY = """
    query BookReviewsByTitle($title: String!, $limit: Int!, $offset: Int!) {
      user_books(
        where: {book: {title: {_eq: $title}}, review: {_is_null: false}}
        order_by: {created_at: desc}
        limit: $limit
        offset: $offset
      ) {
        id
        rating
        review
        review_has_spoilers
        created_at
        user {
          id
          username
        }
      }
    }
"""


BOOK_REVIEWS_QUERY = """
    query BookReviews($book_id: Int!, $limit: Int!, $offset: Int!) {
      user_books(
        where: {book_id: {_eq: $book_id}, review: {_is_null: false}}
        order_by: {created_at: desc}
        limit: $limit
        offset: $offset
      ) {
        id
        rating
        review
        review_has_spoilers
        created_at
        user {
          id
          username
        }
      }
    }
"""
