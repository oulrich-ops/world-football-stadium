import logging
import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

logger = logging.getLogger(__name__)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/117.0.0.0 Safari/537.36"
}

NO_IMAGE = "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0a/No-image-available.png/480px-No-image-available.png"


def get_data_from_wikipedia(url: str):
    """
    Extract data from Wikipedia API.
    """

    logger.info(f"start getting data from {url}")

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        return response.text
    except requests.RequestException as e:
        logger.error(f"Error fetching data from {url}: {e}")
        return None


def extract_data_from_text(html_content: str, ti=None):
    soup = BeautifulSoup(html_content, "html.parser")
    tables = soup.find_all("table", {"class": "wikitable sortable sticky-header"})[0]

    table_rows = tables.find_all("tr")
    logger.info(f"Extracted {len(table_rows)} rows from the table.")

    data = []

    for i in range(1, len(table_rows)):
        tds = table_rows[i].find_all("td")

        values = {
            "rank": i,
            "stadium": clean_text(tds[0].text.strip()),
            "capacity": clean_text(tds[1].text.strip()).replace(",", ""),
            "region": clean_text(tds[2].text.strip()),
            "country": clean_text(tds[3].text.strip()),
            "city": clean_text(tds[4].text.strip()),
            "image": "https://" + tds[5].find("img").get("src").split("//")[1]
            if tds[5].find("img")
            else "NO_IMAGE",
            "home_team": clean_text(tds[6].text.strip()),
        }
        data.append(values)

    df = pd.DataFrame(data)
    df.to_csv("data/football_stadiums.csv", index=False)

    return data


def clean_text(text: str) -> str:
    text = text.replace("\n", " ").replace("\r", " ").strip()
    if text.find("♦"):
        text = text.replace("♦", "").strip()

    if text.find("[") != -1:
        text = text[: text.find("[")].strip()

    if text.find("(formerly)") != -1:
        text = text[: text.find("(formerly)")].strip()

    return text


def get_coordinates(country: str, city: str):
    geolocator = Nominatim(user_agent="stadium_locator")

    try:
        location = geolocator.geocode(f"{city}, {country}", timeout=10)
        if location:
            return location.latitude, location.longitude
        else:
            return None, None
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        logger.error(f"Geocoding error for {city}, {country}: {e}")
        return None, None


def transform_data(data):
    logger.info(data)
    df = pd.DataFrame(data)

    df["capacity"] = (
        pd.to_numeric(df["capacity"], errors="coerce").fillna(0).astype(int)
    )
    df["location"] = df.apply(
        lambda row: get_coordinates(row["country"], row["stadium"]), axis=1
    )
    df["image"] = df["image"].apply(
        lambda x: NO_IMAGE if x in ["NO_IMAGE", "", None] else x
    )

    duplicates = df[df.duplicated(subset=["location"], keep=False)].copy()
    duplicates["location"] = duplicates.apply(
        lambda x: get_coordinates(x["country"], x["city"]), axis=1
    )
    df.update(duplicates)

    return df.to_json(orient="records")


def load_data(json_data):
    df = pd.read_json(json_data)

    file_name = "stadiums_data" + pd.Timestamp.now().strftime("%Y%m%d%H%M%S") + ".csv"
    df.to_csv(
        "abfs://footballdataeng@footdataeng.dfs.core.windows.net/data/" + file_name,
        storage_options={"account_key": ""},
        index=False,
    )

    df.to_csv(f"data/{file_name}", index=False)


#
