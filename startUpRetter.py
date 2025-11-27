import sqlite3

import requests
from bs4 import BeautifulSoup

DATABASE_FILE = "startups.db"


# Returns Cursor of DB and creates File if neccessary
def connectToDb():
    conn = sqlite3.connect(DATABASE_FILE)
    if conn:
        return conn.cursor()
    else:
        raise ("Could'nt connect with db")


with requests.session() as session:
    max_pages = int(input("How many pages?"))
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
                filtered_items[link["title"]] = {
                    "title": link["title"],
                    "href": link["href"],
                }

    for startup in filtered_items:
        resp = session.get(filtered_items[startup]["href"])

        soup = BeautifulSoup(resp.text, "html.parser")

        links = soup.select(".startup-links")

        if len(links) > 0:
            links = links[0]
        else:
            continue

        email = links.select(".email")
        website = links.select(".hp")
        telephone = links.select(".call")
        if len(email):
            filtered_items[startup]["email"] = email[0]["href"][7:]
        if len(website):
            filtered_items[startup]["website"] = website[0]["href"]
        if len(telephone):
            filtered_items[startup]["telephone"] = telephone[0]["href"][4:]

        founder = soup.select(".info-card.founder-year .info-value")
        if len(founder) > 0:
            filtered_items[startup]["year"] = founder[0].text

        print(filtered_items[startup])

    print(f"Found {len(filtered_items)} startups")
    print("Start insertion into database")
