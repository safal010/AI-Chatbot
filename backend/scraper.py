import requests
from bs4 import BeautifulSoup

BASE_URL = "https://insyde.ai"

URLS = [
    "/",
    "/features/",
    "/ai-agent/",
    "/voice-agent/",
    "/usecase/custom-knowledge-base-agents/",
    "/company/",
    "/security-and-trust/",
]


def scrape_page(url):
    response = requests.get(url, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    for element in soup(["script", "style", "nav", "footer"]):
        element.decompose()

    text = soup.get_text(separator=" ", strip=True)

    return text


def scrape_website():
    all_text = ""

    for path in URLS:
        url = BASE_URL + path

        print(f"Scraping: {url}")

        try:
            text = scrape_page(url)

            all_text += f"\n\nSOURCE: {url}\n\n"
            all_text += text

            print(f"  Characters: {len(text)}")

        except Exception as error:
            print(f"  Failed: {error}")

    return all_text


if __name__ == "__main__":
    text = scrape_website()

    print("\nWebsite scraping completed!")
    print("Total characters:", len(text))

    print("\nFirst 2000 characters:\n")
    print(text[:2000])