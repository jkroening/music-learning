import json
from flask import Flask, request, redirect, g, render_template
import requests
import base64
import time
import urllib
import threading
import sys
import csv
import webbrowser
from unidecode import unidecode
from spotify_methods import searchSpotifyTrack

# Authentication Steps, paramaters, and responses are defined at https://developer.spotify.com/web-api/authorization-guide/
# Visit this url to see all the steps, parameters, and expected response.

artist = sys.argv[1]
track = sys.argv[2]
if len(sys.argv) > 3:
    album = sys.argv[3]
else:
    album = None

tracks = searchSpotifyTrack(artist, track, album)

app = Flask(__name__)

with open("../config/config.csv", "U") as f:
    reader = csv.reader(f)
    config = {}
    for row in reader:
        config[row[0]] = row[1]

#  Client Keys
CLIENT_ID = config['SPOTIFY_APP_ID']
CLIENT_SECRET = config['SPOTIFY_APP_SECRET']

# Spotify URLS
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)

# Server-side Parameters
CLIENT_SIDE_URL = "http://127.0.0.1"
PORT = 8080
REDIRECT_URI = "{}:{}/callback/q".format(CLIENT_SIDE_URL, PORT)
SCOPE = "playlist-modify-public playlist-modify-private playlist-read-private"
STATE = ""
SHOW_DIALOG_bool = True
SHOW_DIALOG_str = str(SHOW_DIALOG_bool).lower()

auth_query_parameters = {
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPE,
    # "state": STATE,
    # "show_dialog": SHOW_DIALOG_str,
    "client_id": CLIENT_ID
}

@app.route("/")
def index():
    # Auth Step 1: Authorization
    url_args = "&".join(["{}={}".format(key,urllib.quote(val)) for key,val in auth_query_parameters.iteritems()])
    auth_url = "{}/?{}".format(SPOTIFY_AUTH_URL, url_args)
    return redirect(auth_url)

@app.route("/callback/q")
def callback():
    # Auth Step 4: Requests refresh and access tokens
    auth_token = request.args['code']
    code_payload = {
        "grant_type": "authorization_code",
        "code": str(auth_token),
        "redirect_uri": REDIRECT_URI
    }
    base64encoded = base64.b64encode("{}:{}".format(CLIENT_ID, CLIENT_SECRET))
    headers = {"Authorization": "Basic {}".format(base64encoded)}
    post_request = requests.post(SPOTIFY_TOKEN_URL, data=code_payload, headers=headers)

    # Auth Step 5: Tokens are Returned to Application
    response_data = json.loads(post_request.text)
    access_token = response_data["access_token"]
    refresh_token = response_data["refresh_token"]
    token_type = response_data["token_type"]
    expires_in = response_data["expires_in"]

    # Auth Step 6: Use the access token to access Spotify API
    authorization_header = {"Authorization":"Bearer {}".format(access_token)}

    # Get profile data
    user_profile_api_endpoint = "{}/me".format(SPOTIFY_API_URL)
    profile_response = requests.get(user_profile_api_endpoint, headers=authorization_header)
    profile_data = json.loads(profile_response.text)

    # Get user playlist data and loop over playlists searching for track name
    matched_playlists = []
    offset1 = 0
    while offset1 == 0 or len(playlist_data['items']) > 0:
        playlist_api_endpoint = "{}/playlists?limit=50&offset={}".format(profile_data["href"], offset1)
        playlists_response = requests.get(playlist_api_endpoint, headers=authorization_header)
        playlist_data = json.loads(playlists_response.text)
        for playlist in playlist_data['items']:
            offset2 = 0
            index = 0
            total = int(playlist['tracks']['total'])
            while index < total:
                track_api_endpoint = "{}/playlists/{}/tracks?offset={}".format(profile_data["href"], playlist['uri'].split(":")[-1], offset2)
                tracks_response = requests.get(track_api_endpoint, headers=authorization_header)
                track_data = json.loads(tracks_response.text)
                while "error" in track_data and int(track_data['error']['status']) != 404:
                    print("API rate limiting in effect...")
                    time.sleep(60)
                    tracks_response = requests.get(track_api_endpoint, headers=authorization_header)
                    track_data = json.loads(tracks_response.text)
                if 'error' in track_data and int(track_data['error']['status']) == 404:
                    break
                for track in track_data['items']:
                    index = index + 1
                    if str(track['track']['uri']) in tracks:
                        matched_playlists.append((unidecode(playlist['name']), "Track #{}".format(index)))
                offset2 = offset2 + 100
        offset1 = offset1 + 50

    # Combine profile and playlist data to display
    display_arr = [profile_data] + matched_playlists
    return render_template("index.html",sorted_array=display_arr)


if __name__ == "__main__":
    threading.Timer(1.25, lambda: webbrowser.open("{}:{}".format(CLIENT_SIDE_URL, PORT)) ).start()
    app.run(debug = True, port = PORT, threaded = True)
