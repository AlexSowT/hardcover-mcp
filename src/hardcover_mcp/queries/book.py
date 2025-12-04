BOOKS_BY_ID_QUERY = """
    query BookByID($id: Int!) {
      books(where: {id: {_eq: $id}}) {
        title
        release_year
        rating
        ratings_count
        reviews_count
        contributions {
          author {
            name
          }
        }
        description
        users_read_count
      }
    }
"""

BOOKS_BY_TITLE_QUERY = """
    query BookByTitle($title: String!, $tagging_count_minimum: Int!) {
      books(where: {title: {_eq: $title}}) {
        title
        release_year
        rating
        ratings_count
        reviews_count
        contributions {
          author {
            name
          }
        }
        description
        users_read_count
        taggings(
          where: {
            tag: {
              count: { _gt: $tagging_count_minimum }
            }
          }
        ) {
          tag {
            tag
            tag_category {
                category 
            }
          }
        }
      }
    }
"""

BOOKS_BY_GENRE_QUERY = """
    query BookByGenre($genre: [String!], $rating_minimum: Int!, $tagging_count_minimum: Int!, $limit: Int!, $offset: Int!) {
      books(
        where: {taggings: {tag: {tag: {_in: $genre}}}, _and: {ratings_count: {_gte: $rating_minimum}}}
        order_by: {release_year: desc_nulls_first}
        limit: $limit
        offset: $offset
      ) {
        title
        release_date
        rating
        ratings_count
        reviews_count
        contributions {
          author {
            name
          }
        }
        description
        users_read_count
        taggings(
          where: {
            tag: {
              count: { _gt: $tagging_count_minimum }
            }
          }
        ) {
          tag {
            tag
            tag_category {
                category 
            }
          }
        }
      }
    }

"""
