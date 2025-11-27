import requests
from bs4 import BeautifulSoup

with requests.session() as session:
    max_pages = 10
    filtered_items = {}

    for page in range(0, max_pages):
        print("Trying page: " + str(page))
        session.cookies.clear_session_cookies()
        resp = session.get(
            "https://www.munich-startup.de/startups/?paging=" + str(page)
        )
        soup = BeautifulSoup(resp.text, "html.parser")

        items = soup.select("div div a")

        for link in items:
            if len(
                link.attrs
            ) == 2 and "https://www.munich-startup.de/startups/" in str(link):
                filtered_items[link["title"]] = [link["title"], link["href"]]
        if len(filtered_items) > 3:
            found = True
    for startup in filtered_items:
        print(filtered_items[startup])
