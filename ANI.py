ANILIST_QUE = """
query ($id: Int) {
  Media (id: $id, type: ANIME) {
    title {
      romaji
      english
      native
    }
    bannerImage
    coverImage {
      large
    }
    description
    genres
    averageScore
    siteUrl
  }
}
"""