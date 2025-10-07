import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import os

load_dotenv()

URL = "https://books.toscrape.com/"
CURRENCY_FROM = os.getenv("CURRENCY_FROM", "GBP")
CURRENCY_TO = os.getenv("CURRENCY_TO", "USD")
MOCK_RATE = float(os.getenv("MOCK_RATE", 1.28))
PRODUCT_LIMIT = 10


def scrape_books(url):
    """Scrape book titles and prices from Books to Scrape."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        response.encoding = "utf-8"  
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to {url}: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    products = soup.select("article.product_pod")

    book_data = []
    for product in products[:PRODUCT_LIMIT]:
        name = product.h3.a["title"]
        price_str = product.select_one(".price_color").text.strip()

        price_clean = (
            price_str.encode("latin1", "ignore").decode("utf-8", "ignore")
        )
        price_clean = price_clean.replace("£", "").replace("Â", "").strip()

        try:
            price_gbp = float(price_clean)
        except ValueError:
            print(f"Skipping book '{name}' due to bad price format: {price_clean}")
            continue

        book_data.append({"name": name, "price_gbp": price_gbp})

    return book_data


def convert_currency(amount, rate):
    """Convert currency using a mock or real rate."""
    return round(amount * rate, 2)


if __name__ == "__main__":
    books = scrape_books(URL)

    if not books:
        print("No data scraped. Exiting.")
        exit()

    for book in books:
        book["price_converted"] = convert_currency(book["price_gbp"], MOCK_RATE)

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    df = pd.DataFrame(books)
    df["timestamp"] = timestamp

    df.to_csv("books_converted.csv", index=False)

    print(f"\n=== Books with Converted Prices ({CURRENCY_FROM} → {CURRENCY_TO}) ===")
    print(df.to_string(index=False))

    plt.figure(figsize=(10, 5))
    plt.bar(df["name"], df["price_gbp"], label=f"Price in {CURRENCY_FROM}")
    plt.bar(df["name"], df["price_converted"], label=f"Price in {CURRENCY_TO}", alpha=0.7)
    plt.xticks(rotation=45, ha="right")
    plt.ylabel("Price")
    plt.title(f"Book Prices: {CURRENCY_FROM} vs {CURRENCY_TO}")
    plt.legend()
    plt.tight_layout()
    plt.show()
