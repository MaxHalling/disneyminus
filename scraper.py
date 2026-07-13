import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass

@dataclass
class Movie:
    title: str
    release_year: str
    quality: str
    runtime: str | None
    poster_url: str
    stream_link: str
    rating: str | None

def scrape_movies(search_term: str, base_url: str, streaming_service: str = "FlixHQ") -> list[Movie]:

    if streaming_service == "FlixHQ":
        url = f"{base_url}/search?keyword={search_term}"
    elif streaming_service == "Lookmovie2":
        url = f"{base_url}/movies/search/?q={search_term}"
    else:
        raise ValueError(f"Unsupported streaming service: {streaming_service}")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        raise e
        return

    soup = BeautifulSoup(response.text, "html.parser")
    movies = []

    if streaming_service == "FlixHQ":
        movie_containers = soup.find_all("div", class_="flw-item")

        for container in movie_containers:

            title = container.find("h3", class_="film-name").get_text(strip=True)
            release_year = container.find("span", class_="fdi-item").get_text(strip=True)
            quality = container.find("div", class_="film-poster-quality").get_text(strip=True)
            try:
                runtime = container.find("span", class_="fdi-duration").get_text(strip=True)
            except AttributeError as e:
                runtime = None
            poster_url = container.find("img", class_="film-poster-img").get('data-src')
            stream_link = container.find("h3", class_="film-name").find("a").get("href")

            movie = Movie(
                title = title,
                release_year = release_year,
                quality = quality,
                runtime = runtime,
                poster_url = poster_url,
                stream_link = stream_link,
                rating = None
            )
            movies.append(movie)
        return movies

    elif streaming_service == "Lookmovie2":
        # Implement scraping logic
        movie_containers = soup.find_all("div", class_="movie-item-style-2 movie-item-style-1 tw-relative")
        for container in movie_containers:

            title = container.find("div", class_="mv-item-infor").find("h6").find("a").get_text(strip=True)
            release_year = container.find("p", class_="year").get_text(strip=True)
            quality = container.find("div", class_="quality-tag").get_text(strip=True)
            rating = container.find("p", class_="rate").find("span").get_text(strip=True)
            poster_url = base_url + container.find("img", class_="lozad").get('data-src')
            stream_link = base_url + container.find("div", class_="image__placeholder").find("a").get("href")

            movie = Movie(
                title = title,
                release_year = release_year,
                quality = quality,
                runtime = None,
                poster_url = poster_url,
                stream_link = stream_link,
                rating = rating
            )
            movies.append(movie)
        return movies

if __name__ == "__main__":
    search_term = input("Enter search term: ").strip()
    base_url = input("Enter base URL: ").strip()
    streaming_service = input("Enter streaming service: ").strip()
    movies = scrape_movies(search_term, base_url, streaming_service)
    print(movies[1])