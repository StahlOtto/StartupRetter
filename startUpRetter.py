import sqlite3

import requests
from bs4 import BeautifulSoup

DATABASE_FILE = "startups.db"
CONN: sqlite3.Connection = None


# Returns Cursor of DB and creates File if neccessary
def connectToDb():
    global CONN
    CONN = sqlite3.connect(DATABASE_FILE)
    if CONN:
        return CONN.cursor()
    else:
        raise ("Could'nt connect with db")


# save the changes and exit db safely
def exitFromDb():
    global CONN
    CONN.commit()
    CONN.close()


# creates if neccessary a table for the StartupTable


def initTables(cursor):
    cursor.execute(
        "Create Table if not exists STARTUPS ( \
        name varchar(100) primary key, \
        href varchar(100), \
        website varchar(100), \
        telephone varchar(100), \
        email varchar(100), \
        year varchar(4) \
    )"
    )


# first get all startups then send requests to each site and get their information
with requests.session() as session:
    max_pages = 250
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
                    "name": link["title"],
                    "href": link["href"],
                }

    print("Getting the information for each startup")

    count = 0
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
        count += 1
        print(f"{count}/{len(filtered_items)} completed")

    print(f"Found {len(filtered_items)} startups")
    print("Start insertion into DB")

    cursor = connectToDb()

    initTables(cursor)

    for startup in filtered_items:
        resp = cursor.execute(
            "Insert into STARTUPS (name,href,website,telephone,email,year) VALUES(?,?,?,?,?,?)",
            (
                filtered_items[startup]["name"],
                filtered_items[startup]["href"],
                filtered_items[startup]["website"],
                filtered_items[startup]["telephone"]
                if "telephone" in filtered_items[startup]
                else None,
                filtered_items[startup]["email"],
                filtered_items[startup]["year"],
            ),
        )
    exitFromDb()
    print("Finished Insertion into DB")
