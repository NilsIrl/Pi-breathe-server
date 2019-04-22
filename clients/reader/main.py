#!/usr/bin/env python3

import reader
import time
import sqlite3
import urllib.request
import json

DOMAIN = "localhost"
DB_PATH = "offline.db"

with open("src.key") as keyfile:
    key = keyfile.read()

location_url = "http://" + DOMAIN + "/location?src=" + key
pollution_url = "http://" + DOMAIN + "/pollution"


def get_location(timestamp):
    lng, lat = 0
    success = True
    try:
        response = urllib.request.urlopen(location_url, timeout=2)
        data = json.load(response)['locations']
        nearest = data[0]
        difference = abs(data[0]['time'] - timestamp)
        for x in data[1:]:  # O(n), not very efficient
            current_diff = abs(x['time'] - timestamp)
            if current_diff < difference:
                nearest = x
                difference = current_diff
        lng = nearest['lng']
        lat = nearest['lat']
    except urllib.URLError:  # If there is no internet connection
        success = False
    return (lng, lat, success)


def main():
    while True:
        time.sleep(60)
        pollution_level = sum(reader.read())
        timestamp = int(time.time())
        with sqlite3.connect(DB_PATH) as conn:
            c = conn.cursor()
            c.execute("CREATE TABLE IF NOT EXISTS pollution (id integer "
                      "primary key asc autoincrement, time integer, pollution "
                      "real NOT NULL)")
            c.execute("INSERT INTO pollution (pollution, time) VALUES"
                      "(:pollution, :time)", {
                          "pollution": pollution_level,
                          "time": timestamp,
                          })
            c.commit()
        success = True
        while success:
            with sqlite3.connect(DB_PATH) as conn:
                c = conn.cursor()
                c.execute("SELECT id, pollution, time FROM pollution LIMIT 1")
                result = c.fetchone()
            lng, lat, success = get_location(result['time'])
            if success:
                result['src'] = key
                result['lng'] = lng
                result['lat'] = lat
                urllib.request.urlopen(pollution_url,
                                       data=urllib.parse.urlencode(result)
                                       .encode())


if __name__ == "__main__":
    main()
