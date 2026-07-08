import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass

@dataclass
class Movie:
    title: str
    release_year: str
    quality: str
    runtime: str
    poster_url: str
    stream_link: str

def scrape_movies(search_term: str, streaming_service: str = "FlixHQ") -> list[Movie]:

    if streaming_service == "FlixHQ":
        url = f"https://flixhq.one/search?keyword={search_term}"
    elif streaming_service == "Lookmovie2":
        url = f"https://www.lookmovie2.to/movies/search/?q={search_term}"
    else:
        raise ValueError(f"Unsupported streaming service: {streaming_service}")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching URL: {e}")
        return

    soup = BeautifulSoup(response.text, "html.parser")
    movie_containers = soup.find_all("div", class_="flw-item")

    movies = []

    for index, container in enumerate(movie_containers, 0):

        title = container.find("h3", class_="film-name").get_text(strip=True)
        release_year = container.find("span", class_="fdi-item").get_text(strip=True)
        quality = container.find("div", class_="film-poster-quality").get_text(strip=True)
        try:
            runtime = container.find("span", class_="fdi-duration").get_text(strip=True)
        except AttributeError as e:
            runtime = "N/A"
            print(e)
        poster_url = container.find("img", class_="film-poster-img").get('data-src')
        stream_link = container.find("h3", class_="film-name").find("a").get("href")

        movie = Movie(
            title = title,
            release_year = release_year,
            quality = quality,
            runtime = runtime if runtime else "N/A",
            poster_url = poster_url,
            stream_link = stream_link
        )
        movies.append(movie)
        if index == 10:
            break

    return movies

if __name__ == "__main__":
    search_term = input("Enter search term: ").strip()
    movies = scrape_movies(search_term)
    print(movies)