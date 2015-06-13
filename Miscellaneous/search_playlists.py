######################
## given a song (artist name and title, album title is optional)
## find any of the user's playlists that
## contain the song

## set spotipy credentials like so:
## export SPOTIPY_CLIENT_ID='your-spotify-client-id'
## export SPOTIPY_CLIENT_SECRET='your-spotify-client-secret'
## export SPOTIPY_REDIRECT_URI='your-app-redirect-url'
######################

import sys
import os
import requests
import time
import pandas as pd
import pdb
import spotipy
from spotipy import util
from unidecode import unidecode
from sklearn import decomposition
from sklearn import preprocessing
from sklearn import cluster
import plotly.plotly as py
from plotly.graph_objs import *
import plotly.tools as tls
import numpy as np

def getSpotifyCred(username):
    SPOTIPY_CLIENT_ID = "93cb0aa1e52240229a3a47eab39c9db3"
    SPOTIPY_CLIENT_SECRET = "cf523e23cba740c5b9169a589716b8dd"
    SPOTIPY_REDIRECT_URI = "http://afireintheattic.com/"
    scope = 'user-library-read'
    token = util.prompt_for_user_token(username, scope, SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI)
    if token:
        sp = spotipy.Spotify(auth = token)
        return sp
    else:
        print "Can't get token for", username

def loadFile(location, filename):
    try:
        with open(os.path.join(location, filename), "U") as f:
            if ".json" in filename:
                infile = json.load(f)
            elif ".csv" in filename:
                infile = pd.io.parsers.read_csv(f)
            elif ".txt" in filename:
                infile = f.readlines()
            else:
                infile = f.read()
    except:
        if ".json" in filename:
            infile = {}
        elif ".csv" in filename:
            infile = pd.DataFrame(index = None, columns = None)
        elif ".txt" in filename:
            infile = []
        else:
            infile = None
    return infile

def lookupSongBySpotifyID(song, df):
    track_id = getSpotifyIDs(song)[0]
    return any(df.spotify_id == track_id)

def callAPI(url, payload = None):
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

def pullEchoNestSong(api_key, track):
    url_base = "http://developer.echonest.com/api/v4/song/profile"
    
    track_id, spotify_uri = getSpotifyIDs(track)

    ## due to echonest using 2 different bucket params and url encoding the ampersand, payload cannot be used
    # payload = {'api_key' : api_key, 'track_id' : spotify_uri, 'bucket' : "audio_summary&bucket=id:spotify", 'format' : "json"}
    url_suffix = "?api_key=%s&track_id=%s&bucket=audio_summary&bucket=id:spotify&format=json" % (api_key, spotify_uri)
    url = url_base + url_suffix
    
    data = callAPI(url)

    ## if response is a success
    if data['response']['status']['code'] == 0:
        ## pop off unneeded data and flatten dict
        song = flattenDictCustom(data['response']['songs'][0])
        song.pop('audio_md5', None)
        song.pop('analysis_url', None)
        song.pop('artist_foreign_ids', None)
        ## add spotify uri to song data
        song['spotify_id'] = track_id
        ## rename keys as necessary
        song['echonest_id'] = song.pop('id')
    elif data['response']['status']['code'] == 5:
        ## the song cannot be found by the spotify id
        track = pullSpotifyTrack(track_id)
        url = "http://developer.echonest.com/api/v4/song/search"
        payload = {'api_key' : api_key, 'artist' : track['artist'], 'title' : track['song'], 'bucket' : "audio_summary", 'format' : "json"}
        data = callAPI(url, payload)
        ## pop off unneeded data and flatten dict
        song = flattenDictCustom(data['response']['songs'][0])
        song.pop('audio_md5', None)
        song.pop('analysis_url', None)
        song.pop('artist_foreign_ids', None)
        ## check to be sure it's the correct song
        if song['artist_name'] == track['artist'] and song['title'] == track['song']:
            ## add spotify uri to song data
            song['spotify_id'] = track_id
            ## rename keys as necessary
            song['echonest_id'] = song.pop('id')
        else:
            print "Song not found via EchoNest search."
    else:
        "Unrecognized error code."

    return song

def pullEchoNestArtist(api_key, artists, db):
    url = "http://developer.echonest.com/api/v4/artist/terms"
    spotify_uri = "spotify:artist:%s" % artist_id
    if "spotify:artist:" in track:
        spotify_uri = track
    else:
        artist_id = stripSpotifyLink(track)
        spotify_uri = "spotify:artist:%s" % artist_id
    payload = {'api_key' : api_key, 'id' : spotify_uri, 'bucket' : "id:spotify"}
    data = callAPI(url, payload)

def pullSpotifyTrack(track_id):
    url = "https://api.spotify.com/v1/tracks/%s" % track_id.strip()
    data = callAPI(url)
    song = unidecode(data['name'])
    album = unidecode(data['album']['name'])
    artist = unidecode(data['artists'][0]['name'])
    artist_id = stripSpotifyURI(data['artists'][0]['uri'])
    track_data = {'song' : song, 'album' : album, 'artist' : artist, 'artist_id' : artist_id, 'popularity' : data['popularity']}
    return track_data

def stripSpotifyLink(http_link):
    spotify_id = str(http_link).replace("https://open.spotify.com/track/", "").strip()
    return spotify_id

def stripSpotifyURI(uri):
    spotify_id = str(uri).split(":")[-1]
    return spotify_id

def getSpotifyIDs(text):
    if "spotify:track:" in text:
        track_id = stripSpotifyURI(text)
        spotify_uri = track
    else:
        track_id = stripSpotifyLink(text)
        spotify_uri = "spotify:track:%s" % track_id
    return track_id, spotify_uri

def searchSpotifyTrack(artist_name, title, album = None):
    url = "https://api.spotify.com/v1/search"
    payload = {'q' : [artist_name, title, album], 'type': "track", 'limit' : 50, 'market' : "US"}
    data = callAPI(url, payload)
    tracks = []
    for i in xrange(len(data['tracks']['items'])):
        if album is not None:
            if unidecode(data['tracks']['items'][i]['artists'][0]['name']).lower() == artist_name.lower() and \
                unidecode(data['tracks']['items'][i]['album']['name']).lower() == album.lower() and \
                unidecode(data['tracks']['items'][i]['name']).lower() == title.lower():
                spotify_uri = data['tracks']['items'][i]['uri']
                tracks.append(str(spotify_uri))
        else:
            if unidecode(data['tracks']['items'][i]['artists'][0]['name']).lower() == artist_name.lower() and \
                unidecode(data['tracks']['items'][i]['name']).lower() == title.lower():
                spotify_uri = data['tracks']['items'][i]['uri']
                tracks.append(str(spotify_uri))
    return tracks

def searchUserPlaylists(sp, user, tracks):
    playlists = sp.user_playlists(user)
    for playlist in playlists['items']:
        if playlist['owner']['id'] == user:
            results = sp.user_playlist(user, playlist['id'], fields="tracks,next")
            ts = results['tracks']
            for t in enumerate(ts['items']):
                # print str(t[1]['track']['uri'])
                if str(t[1]['track']['uri']) in tracks:
                    # print tracks[1]
                    print "\n" + playlist['name']
                    print "Track #%s" % (t[0] + 1)


def main():

    # ## load tracks in playlist
    artist_name = sys.argv[1]
    title = sys.argv[2]
    if len(sys.argv) > 3:
        album = sys.argv[3]
    else:
        album = None

    username = "kroening"

    sp = getSpotifyCred(username)
    
    tracks= searchSpotifyTrack(artist_name, title, album)

    searchUserPlaylists(sp, username, tracks)
    print "\n"

if __name__ == "__main__":
    main()