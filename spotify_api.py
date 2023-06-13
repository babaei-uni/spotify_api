import sqlite3
from dotenv import load_dotenv
import os
import base64
from requests import post, get
import json

load_dotenv()


client_id = os.getenv("Client_ID")
client_secret = os.getenv("Client_secret")


# this is the first function of the project to get the token
def get_token():
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode("utf-8")
    auth_base64 = str(base64.b64encode(auth_bytes), "utf-8")

    url = "https://accounts.spotify.com/api/token"
    # headers = {
    #    "Authorization": "Basic " + auth_base64,
    #    "Content-Type": "application/json-www-form-urlencoded",
    # }
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded",
    }

    data = {"grant_type": "client_credentials"}

    result = post(url, headers=headers, data=data)
    print(result)
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    return token


# function get_auth_header : to get the header of the token
def get_auth_header(token):
    return {"Authorization": "Bearer " + token}


# function search_for_artist : to find artist id by their name and save their unique id in a dictionary
def search_for_artist(token, artist_name, artists_id):
    url = "https://api.spotify.com/v1/search"
    headers = get_auth_header(token)
    query = f"?q={artist_name}&type=artist&limit=1"
    query_url = url + query
    result = get(query_url, headers=headers)
    json_result = json.loads(result.content)["artists"]["items"]
    if len(json_result) <= 0:
        print("No artist found")
        return None
    artists_id[artist_name] = (json_result[0]["id"], json_result[0]["name"])


# function get_songs_by_artist : to get the songs of the artist by its unique id
def get_songs_by_artist(token, artist_id):
    url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks?country=US"
    headers = get_auth_header(token)
    result = get(url, headers=headers)
    json_result = json.loads(result.content)
    return json_result


# function Json_extraction : to extract the data we need from the json we take from the function get_songs_by_artist
def Json_extraction(json):
    # you can see a sample of the json in the file songs.txt
    album_realese_date = json["album"]["release_date"]
    album_total_tracks = json["album"]["total_tracks"]
    album_name = json["album"]["name"]
    artist_name = json["artists"][0]["name"]
    track_name = json["name"]
    track_duration_s = int(json["duration_ms"] / 1000)
    track_popularity = json["popularity"]
    place_in_album = json["track_number"]
    track_explicity = json["explicit"]
    return [
        # about album
        album_realese_date,
        album_total_tracks,
        album_name,
        # about artist
        artist_name,
        # about track
        track_name,
        track_duration_s,
        track_popularity,
        place_in_album,
        track_explicity,
    ]


token = get_token()


# i did get_artist_id_from_txt once and at last i saved the artists_id in the file artist_id.json so i dont have to run it again
def get_artist_id_from_txt(token):
    list_of_best_US_artists = []
    # this file is a list of best US singers
    f = open("list_of_best_US_singers.txt")
    for i in f:
        if i[
            0
        ].isalpha():  # to ignore the lines we dont need and just get the names of singers
            list_of_best_US_artists.append(i.strip())

    f.close()  # close the file

    ids_artist = {}
    print(list_of_best_US_artists)

    for artist in list_of_best_US_artists:
        print(artist)
        search_for_artist(token, artist, ids_artist)

    # Specify the file path where you want to save the dictionary
    file_path = "artists_id.json"

    # Open the file in write mode and write the dictionary as JSON
    with open(file_path, "w") as file:
        json.dump(ids_artist, file)


try:
    print("we have already the artists_id.json file")
    ids_artist = json.load(open("artists_id.json"))
except:
    get_artist_id_from_txt(
        token
    )  # if the file artist_id.json doesnt exist we will create it by running this function


############################################################################

# this is data base part :))


conn = sqlite3.connect("spotify.db")
cur = conn.cursor()


# I will Create a new database and ignore the previous one :
def delete_table():
    cur.executescript(
        """
    DROP TABLE IF EXISTS Artist;
    DROP TABLE IF EXISTS Album;
    DROP TABLE IF EXISTS Track;
    """
    )


# if we want to delete the previous tables of spotify.db we can run delete_table
delete_table_stage = input(
    "Do you want to delete the previous tables of spotify.db? (y/n) : "
)
if delete_table_stage == "y":
    delete_table()


# Create tables in the database :
def create_table():
    cur.executescript(
        """
    CREATE TABLE Artist (
        id  INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        name    TEXT UNIQUE
    );
    CREATE TABLE Album (
        id  INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        artist_id  INTEGER,
        title   TEXT UNIQUE,
        realese_date VARCHAR(15),
        total_tracks INTEGER
    );
    CREATE TABLE Track (
        id  INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
        title TEXT  UNIQUE,
        album_id  INTEGER,
        duration_s INTEGER,
        popularity INTEGER,
        place_in_album INTEGER,
        explicity INTEGER
    );
    """
    )


create_table_stage = input(
    "Do you want to create the tables of spotify.db? (y/n) : ")

if create_table_stage == "y":
    create_table()


# insert data into the tables
def insert_artist(artist_name):
    cur.execute(
        """INSERT OR IGNORE INTO Artist (name) VALUES (?)""",
        (artist_name,),
    )


def insert_album(album_name, album_realese_date, album_total_tracks, artist_name):
    artist_id = cur.execute(
        """SELECT id FROM Artist WHERE name = ?""", (artist_name,)
    ).fetchone()[0]
    cur.execute(
        """INSERT OR IGNORE INTO Album (title,artist_id,realese_date,total_tracks) VALUES (?,?,?,?)""",
        (
            album_name,
            artist_id,
            album_realese_date,
            album_total_tracks,
        ),
    )


def insert_track(
    track_name,
    track_duration_s,
    track_popularity,
    place_in_album,
    track_explicity,
    album_name,
):
    album_id = cur.execute(
        """SELECT id FROM Album WHERE title = ?""", (album_name,)
    ).fetchone()[0]
    cur.execute(
        """INSERT OR IGNORE INTO Track (title,album_id,duration_s,popularity,place_in_album,explicity) VALUES (?,?,?,?,?,?)""",
        (
            track_name,
            album_id,
            track_duration_s,
            track_popularity,
            place_in_album,
            track_explicity,
        ),
    )


for artist in ids_artist:
    name = ids_artist[artist][1]
    id = ids_artist[artist][0]
    exist_in_db = cur.execute(
        """SELECT id FROM Artist WHERE name = ?""", (name,)
    ).fetchone()
    if exist_in_db is not None:
        # if the artist is already in the database we will skip it,because it means that we already have the data of his songs from the previous runs
        continue
    print(f"extracting data for {artist}")
    a = get_songs_by_artist(token, id)

    for song in range(len(a["tracks"])):
        b = Json_extraction(a["tracks"][song])
        # i want to check if b[3] is exist or not in db
        exist_in_db = cur.execute(
            """SELECT id FROM Artist WHERE name = ?""", (b[3],)
        ).fetchone()
        if exist_in_db is None:
            insert_artist(b[3])
        exist_in_db = cur.execute(
            """SELECT id FROM Album WHERE title = ?""", (b[2],)
        ).fetchone()
        if exist_in_db is None:
            insert_album(b[2], b[0], b[1], b[3])
        insert_track(b[4], b[5], b[6], b[7], b[8], b[2])
    conn.commit()
