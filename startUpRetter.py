import sqlite3
import traceback

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
    cursor.execute("drop table if exists startups")
    cursor.execute(
        "Create Table STARTUPS ( \
        name varchar(100) primary key, \
        description varchar(1000), \
        category varchar(200), \
        href varchar(100), \
        website varchar(100), \
        telephone varchar(100), \
        email varchar(100), \
        year varchar(4) \
    )"
    )


# first get all startups then send requests to each site and get their information
with requests.session() as session:
    max_startups = 10  # gets automatically updated to the correct value
    filtered_items = {}
    page = 1
    pagesize = 20
    print("fetching urls to later gather additional info")
    while len(filtered_items) < max_startups:
        print(f"{len(filtered_items)} / {max_startups} urls fetched")
        session.cookies.clear_session_cookies()
        resp = session.get(
            f"https://www.munich-startup.de/wp-admin/admin-ajax.php?action=filter_startups&limit={
                pagesize
            }&paging={page}&ecosystem_type=startup"
        )
        page += 1

        objects = resp.json()
        if "total" not in objects:
            break
        max_startups = objects["total"]

        items = objects["startups"]
        for link in items:
            link = items[link]
            filtered_items[link["title"]] = {
                "name": link["title"],
                "href": link["permalink"],
                "category": link["terms"][0]["name"]
                if link["terms"] and len(link["terms"]) > 0
                else None,
                "description": link["description"],
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
        try:
            resp = cursor.execute(
                "Insert into STARTUPS (name,href,description, category, website,telephone,email,year) VALUES(?,?,?,?,?,?,?, ?)",
                (
                    filtered_items[startup]["name"],
                    filtered_items[startup]["href"],
                    filtered_items[startup]["description"]
                    if "description" in filtered_items[startup]
                    else None,
                    filtered_items[startup]["category"]
                    if "category" in filtered_items[startup]
                    else None,
                    filtered_items[startup]["website"]
                    if "website" in filtered_items[startup]
                    else None,
                    filtered_items[startup]["telephone"]
                    if "telephone" in filtered_items[startup]
                    else None,
                    filtered_items[startup]["email"]
                    if "email" in filtered_items[startup]
                    else None,
                    filtered_items[startup]["year"]
                    if "year" in filtered_items[startup]
                    else None,
                ),
            )
        except Exception as e:
            print(f"Insertion for {filtered_items[startup]['name']} failed")
            traceback.print_exc(e)

    exitFromDb()
    print("Finished Insertion into DB")
