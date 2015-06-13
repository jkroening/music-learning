######################
## take an itunes exported playlist
## and find all the songs in spotify
## output a list of matching spotify ids
######################

import sys
import csv
import time
import urllib
import requests

def callAPI(url, payload):
    try:
        response = requests.get(url, params = payload)
        # if rate limit is about to be exceeded, wait for one minute so it can reset (~120 requests allowed per minute)
        if "x-ratelimit-remaining" in response.headers and int(response.headers.get('x-ratelimit-remaining')) < 5:
            time.sleep(60)
        data = response.json()
    except:
        print("Trouble with API call: %s") % url
        time.sleep(2)
        return callAPI(url, payload)
    return data

def searchSpotifyTrack(name, artist, album):
    url = "http://ws.spotify.com/search/1/track.json?q=%s&territory=US" % (name + " " + artist + " " + album)
    data = callAPI(url, None)
    if len(data['tracks']) == 0:
        return ""
    else:
        track_id = data['tracks'][0]['href']
        return track_id


def main():
    playlist_file = sys.argv[1]

    outlist = []

    with open(playlist_file, "U") as f:
        for line in csv.reader(f, dialect = "excel-tab"):
            if "Date Modified" in line:
                continue
            name = line[0].replace("&", "%26").strip()
            artist = line[1].replace("&", "%26").strip()
            album = line[3].replace("&", "%26").replace("|EFA|", "").replace("[EFA]", "").replace("[EP]", "").strip()
            if "B-Sides" in album:
                album = ""
            print (name, artist, album)
            outlist.append(searchSpotifyTrack(name, artist, album))

    with open("output/spotify_tracks.txt", "w") as f:
        for item in outlist:
            f.write("%s\n" % item)


if __name__ == "__main__":
    main()