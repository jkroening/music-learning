# import sys
import os
# sys.path.append("../Modules")
from unidecode import unidecode
from flask import Flask, redirect, url_for, session, request, g, render_template
from flask_oauthlib.client import OAuth, OAuthException
import spotipy
from spotipy import util, oauth2
import json
import urllib3
import urllib
import base64
import fileinput
import requests
import re
import csv
import pdb
import module_helpers as mhlpr
import helpers as hlpr


with open("../config/config.csv", "U") as f:
    reader = csv.reader(f)
    config = {}
    for row in reader:
        config[row[0]] = row[1]

SPOTIPY_USERNAME = config['SPOTIFY_USERNAME']
SPOTIPY_CLIENT_ID = config['SPOTIFY_CLIENT_ID']
SPOTIPY_CLIENT_SECRET = config['SPOTIFY_CLIENT_SECRET']
SPOTIPY_REDIRECT_URI = config['SPOTIFY_REDIRECT_URI']
SPOTIPY_SCOPE = config['SPOTIFY_SCOPE']

# os.environ['SPOTIPY_USERNAME'] = config['username']
# os.environ['SPOTIPY_CLIENT_ID'] = SPOTIPY_CLIENT_ID
# os.environ['SPOTIPY_CLIENT_SECRET'] = SPOTIPY_CLIENT_SECRET
# os.environ['SPOTIPY_REDIRECT_URI'] = SPOTIPY_REDIRECT_URI
# os.environ['SPOTIPY_SCOPE'] = 'user-library-read'

def authSpotipy(SPOTIPY_CLIENT_ID = None, SPOTIPY_CLIENT_SECRET = None):

    auth = oauth2.SpotifyClientCredentials(
        client_id = SPOTIPY_CLIENT_ID,
        client_secret = SPOTIPY_CLIENT_SECRET
    )

    token = auth.get_access_token()

    return token

    # token = util.prompt_for_user_token(
    #     username = os.environ['SPOTIPY_USERNAME'],
    #     scope = os.environ['SPOTIPY_SCOPE']
    # )

    # token = util.prompt_for_user_token(
    #     username = os.environ['SPOTIPY_USERNAME'],
    #     client_id = os.environ['SPOTIPY_CLIENT_ID'],
    #     client_secret = os.environ['SPOTIPY_CLIENT_SECRET'],
    #     redirect_uri = os.environ['SPOTIPY_REDIRECT_URI']
    # )

    # sp = spotipy.Spotify(auth = token)

    # return sp

def getSpotifyCred():
    with open("../config/config.csv", "U") as f:
        reader = csv.reader(f)
        config = {}
        for row in reader:
            config[row[0]] = row[1]

    SPOTIPY_USERNAME = config['SPOTIFY_USERNAME']
    SPOTIPY_CLIENT_ID = config['SPOTIFY_CLIENT_ID']
    SPOTIPY_CLIENT_SECRET = config['SPOTIFY_CLIENT_SECRET']
    SPOTIPY_REDIRECT_URI = config['SPOTIFY_REDIRECT_URI']
    SPOTIPY_SCOPE = config['SPOTIFY_SCOPE']
    ## token = util.prompt_for_user_token(SPOTIPY_USERNAME, SPOTIPY_SCOPE, SPOTIPY_CLIENT_ID,
    #                                    SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI)
    ## print(token)
    # spauth = spotipy.SpotifyOAuth(
    #     client_id = SPOTIPY_CLIENT_ID,
    #     client_secret = SPOTIPY_CLIENT_SECRET,
    #     redirect_uri = SPOTIPY_REDIRECT_URI,
    #     scope = SPOTIPY_SCOPE,
    #     username = SPOTIPY_USERNAME
    # )
    # sp = spotipy.Spotify(auth_manager = spauth)

    auth = oauth2.SpotifyClientCredentials(
        client_id = SPOTIPY_CLIENT_ID,
        client_secret = SPOTIPY_CLIENT_SECRET
    )
    sp = spotipy.Spotify(client_credentials_manager = auth)

    return(sp)
    # if token:
    #     sp = spotipy.Spotify(auth = token)
    #     return sp
    # else:
    #     print("Can't get token for", username)

def retrySpotipy(func):
    # token = util.prompt_for_user_token(
    #     username = os.environ['SPOTIPY_USERNAME'],
    #     scope = os.environ['SPOTIPY_SCOPE']
    # )
    def retry(*args, **kwargs):
        try:
            auth = oauth2.SpotifyClientCredentials(
                client_id = SPOTIPY_CLIENT_ID,
                client_secret = SPOTIPY_CLIENT_SECRET
            )
            token = auth.get_access_token()
            kwargs['token'] = token
            return func(*args, **kwargs)
        except Exception as e:
            print(e)
    return retry

def getSpotifyTrackIDs(text):
    if "spotify:track:" in text:
        track_id = stripSpotifyURI(text)
        spotify_uri = text
    else:
        track_id = stripSpotifyLink(text)
        spotify_uri = "spotify:track:%s" % track_id
    return track_id, spotify_uri

def getSpotifyArtistIDs(text):
    if "spotify:artist:" in text:
        artist_id = stripSpotifyURI(text)
        spotify_uri = text
    else:
        artist_id = stripSpotifyLink(text)
        spotify_uri = "spotify:artist:%s" % artist_id
    return artist_id, spotify_uri

def getSpotifyAlbumIDs(text):
    if "spotify:album:" in text:
        album_id = stripSpotifyURI(text)
        spotify_uri = text
    else:
        album_id = stripSpotifyLink(text)
        spotify_uri = "spotify:album:%s" % album_id
    return album_id, spotify_uri

@retrySpotipy
def getAudioFeatures(tracks, token = None, silent = False, sptpy = None):
    if sptpy is None and token is not None:
        sptpy = spotipy.Spotify(auth = token)
    out = []
    if isinstance(tracks, str) and not re.search('local', tracks[0]):
        data = sptpy.audio_features([tracks])
        out = parseAudioFeatures(data[0], tracks, silent, token = token, sptpy = sptpy)
    elif len(tracks) > 50:
        chunks = mhlpr.chunker(tracks, 50)
        for chunk in chunks:
            ## don't try local tracks
            data = sptpy.audio_features(
                tracks = ["" if re.search('local', x) else x for x in chunk]
            )
            for d, c in zip(data, chunk):
                out.append(parseAudioFeatures(d, c, silent, token = token, sptpy = sptpy))
    else:
        ## don't try local tracks
        data = sptpy.audio_features(
            tracks = ["" if re.search('local', x) else x for x in tracks]
        )
        for d, t in zip(data, tracks):
            out.append(parseAudioFeatures(d, t, silent, token = token, sptpy = sptpy))
    return out

def getArtistGenres(artist_id, token = None, sptpy = None):
    if sptpy is None and token is not None:
        sptpy = spotipy.Spotify(auth = token)
    return sptpy.artist(artist_id)['genres']

@retrySpotipy
def getArtistsGenres(artists, token = None):
    if sptpy is None and token is not None:
        sptpy = spotipy.Spotify(auth = token)
    out = []

    if isinstance(artists, str):
        artists = [artists]
    elif len(artists) > 50:
        chunks = mhlpr.chunker(artists, 50)
        for chunk in chunks:
            ## don't try local tracks
            data = sptpy.artist(
                artists = ["" if re.search('local', x) else x for x in chunk]
            )
            for d, c in zip(data, chunk):
                out.append(parseAudioFeatures(d, c, token = token, sptpy = sptpy))
    else:
        ## don't try local tracks
        data = sptpy.audio_features(
            tracks = ["" if re.search('local', x) else x for x in tracks]
        )
        for d, t in zip(data, tracks):
            out.append(parseAudioFeatures(d, t, token = token, sptpy = sptpy))

    return out

def parseGenres(artist, uri):
    ## if response is a success
    if artist is not None:
        1 == 1

def parseAudioFeatures(song, uri, silent = False, token = None, sptpy = None):
    ## if response is a success
    if song is not None:
        track = pullSpotifyTrack(stripSpotifyURI(song['uri']), token = token, sptpy = sptpy)
        song['artist'] = track['artist']
        song['title'] = track['title']
        song['album'] = track['album']
        song['spotify_artist_id'] = track['spotify_artist_id']
        song['spotify_album_id'] = track['spotify_album_id']
        album = pullSpotifyAlbum(song['spotify_album_id'], token = token, sptpy = sptpy)
        song['release_date'] = album['release_date']
        song['year'] = float(album['year'])
        song['duration'] = song.pop('duration_ms') / 1000.0
        ## add spotify uri to song data
        song['spotify_id'] = stripSpotifyURI(song.pop('uri'))
        ## pop off unneeded data and flatten dict
        song.pop('track_href', None)
        song.pop('analysis_url', None)
        song.pop('type', None)
        song.pop('id', None)
    elif not silent:
        print("Song audio features not found: {}".format(uri))
    return song

def pullSpotifyTrack(track_id, token = None, sptpy = None):
    if sptpy is None and token is not None:
        sptpy = spotipy.Spotify(auth = token)
    data = sptpy.track(track_id.strip())
    song = unidecode(data['name'])
    album = unidecode(data['album']['name'])
    artist = unidecode(data['artists'][0]['name'])
    artist_id = stripSpotifyURI(data['artists'][0]['uri'])
    album_id = stripSpotifyURI(data['album']['uri'])
    if len(data['artists']) > 1:
        secondary_artist = stripSpotifyURI(data['artists'][1]['uri'])
    else:
        secondary_artist = None
    track_data = {'title' : song, 'album' : album, 'spotify_id' : track_id.strip(), 'artist' : artist, 'spotify_artist_id' : artist_id, 'spotify_album_id' : album_id, 'popularity' : data['popularity'], 'secondary_artist' : secondary_artist}
    return track_data

def pullSpotifyTracks(location, filename, tracks = [], local_tracks = [], album_info = False, token = None, sptpy = None):
    ## set spotify auth
    config = hlpr.loadFile("../config", "config.csv", True)
    if sptpy is None and token is not None:
        sptpy = spotipy.Spotify(auth = token)
    sptpy = getSpotifyCred()
    ## load tracks in playlist
    in_tracks = hlpr.loadFile(location, filename)
    for track in in_tracks:
        if 'local' in track:
            local_tracks.append(track)
            continue
        track_id = stripSpotifyLink(track)
        track_data = pullSpotifyTrack(track_id, token = token, sptpy = sptpy)
        if album_info:
            album_data = pullSpotifyAlbum(track_data['spotify_album_id'], token = token, sptpy = sptpy)
            track_data['release_date'] = album_data['release_date']
            track_data['year'] = album_data['year']
        tracks.append(track_data)
    return tracks, local_tracks

def pullSpotifyArtist(artist_id, token = None, sptpy = None):
    if sptpy is None and token is not None:
        sptpy = spotipy.Spotify(auth = token)
    data = sptpy.artist(artist_id.strip())
    genres = data['genres']
    name = data['name']
    popularity = data['popularity']
    artist_data = {'artist' : name, 'spotify_artist_id' : artist_id, 'genres' : genres, 'artist_popularity' : popularity}
    return artist_data

def pullSpotifyAlbum(album_id, token = None, sptpy = None):
    if sptpy is None and token is not None:
        sptpy = spotipy.Spotify(auth = token)
    data = sptpy.album(album_id.strip())
    album_name = unidecode(data['name'])
    artist = unidecode(data['artists'][0]['name'])
    artist_id = stripSpotifyURI(data['artists'][0]['uri'])
    release_date = data['release_date']
    if data['release_date_precision'] == 'day':
        year = release_date[0:4]
    elif data['release_date_precision'] == 'year':
        year = release_date
    album_data = {'album_name' : album_name, 'artist' : artist, 'spotify_artist_id' : artist_id, 'release_date' : release_date, 'year' : year, 'genres' : data['genres']}
    return album_data

@retrySpotipy
def searchSpotifyTrack(artist, title, album = None, first = False, token = None, sptpy = None):
    if sptpy is None and token is not None:
        sptpy = spotipy.Spotify(auth = token)
    data = sptpy.search(q = "%s %s %s" % (artist, title, album), limit = 50, type = 'track')

    tracks = []
    for i in xrange(len(data['tracks']['items'])):
        if album is not None:
            if unidecode(data['tracks']['items'][i]['artists'][0]['name']).lower() == artist.lower() and \
                unidecode(data['tracks']['items'][i]['album']['name']).lower() == album.lower() and \
                unidecode(data['tracks']['items'][i]['name']).lower() == title.lower():
                spotify_uri = data['tracks']['items'][i]['uri']
                tracks.append(str(spotify_uri))
        else:
            if unidecode(data['tracks']['items'][i]['artists'][0]['name']).lower() == artist.lower() and \
                unidecode(data['tracks']['items'][i]['name']).lower() == title.lower():
                spotify_uri = data['tracks']['items'][i]['uri']
                tracks.append(str(spotify_uri))
    if not len(tracks):
        return None
    if first:
        return tracks[0]
    else:
        return tracks

def stripSpotifyLink(http_link):
    if 'local' in http_link:
        return http_link.strip()
    else:
        spotify_id = str(http_link).replace("https://open.spotify.com/track/", "").strip()
        return spotify_id

def stripSpotifyURI(uri):
    spotify_id = str(uri).split(":")[-1].strip()
    return spotify_id

def formatLocalTrack(link):
    s = link.split("local/")[1]
    artist = urllib.parse.unquote(s.split("/")[0])
    title = urllib.parse.unquote(s.split("/")[2])
    album = urllib.parse.unquote(s.split("/")[1])
    return artist, title, album

def writeIDsToURI(ids, location, filename):
    with open(os.path.join(location, filename), "w") as f:
        for i in ids:
            f.write("spotify:track:%s\n" % i)

def getTermStats(term):
    term_freq = "%s_freq" % term['name'].replace(" ", "_")
    term_wt = "%s_wt" % term['name'].replace(" ", "_")
    freq = term['frequency']
    wt = term['weight']
    return term_freq, term_wt, freq, wt

## DEPRECATED -- since Echo Nest was purchased by Spotify
def pullArtistTerms(api_key, artist, related_artists = None, related_artist_index = 0, term_min = 0):
    """
    Function to get artist terms and their weights and frequencies.

    @param  related_artists:  artists related to artist, if None, then the terms being gathered are for the artist and not a related artist
    @param  related_artist_index:  the index of the current related artist being evaluated as a terms proxy for the artist
    @param  term_min:  the minimum number of terms that is permitted.
                                   for related_artists this is usually set to 3 to safe-guard against gathering terms from a lesser-known related artist
    """

    url = "http://developer.echonest.com/api/v4/artist/terms"

    spotify_uri = "spotify:artist:%s" % artist['spotify_artist_id']
    payload = {'api_key' : api_key, 'id' : spotify_uri, 'format' : "json"}

    data = mhlpr.callAPI(url, payload)

    # get terms from json
    terms = data['response']['terms']
    if len(terms) > term_min:
        for term in terms:
            term_freq, term_wt, freq, wt = getTermStats(term)
            ## frequency as metric
            artist[term_freq] = freq
            ## frequency * weight as metric
            term_freqwt = "%swt" % term_freq
            artist[term_freqwt] = freq * wt
            ## weight as metric
            artist[term_wt] = wt
        return artist
    else:
        # there are no terms for this artist
        # so search for related artists and get their terms
        if related_artists is None:
            url = "https://api.spotify.com/v1/artists/%s/related-artists" % artist['spotify_artist_id']

            spotify_data = mhlpr.callAPI(url)

            related_artists = spotify_data['artists']
            related_artist_id = {'spotify_artist_id' : sptfy.stripSpotifyURI(related_artists[0]['uri'])}
        else:
            related_artist_id = {'spotify_artist_id' : sptfy.stripSpotifyURI(related_artists[related_artist_index]['uri'])}

        return pullArtistTerms(api_key, related_artist_id, related_artists, int(related_artist_index + 1), 3)

def searchUserPlaylists(sp, user, tracks):
    playlists = sp.user_playlists(user)
    for playlist in playlists['items']:
        if playlist['owner']['id'] == user:
            results = sp.user_playlist(user, playlist['id'], fields="tracks,next")
            ts = results['tracks']
            for t in enumerate(ts['items']):
                # print(str(t[1]['track']['uri']))
                if str(t[1]['track']['uri']) in tracks:
                    # print(tracks[1])
                    print("\n" + playlist['name'])
                    print("Track #%s" % (t[0] + 1))

def followArtist(artists, token = None, sptpy = None):
    if sptpy is None and token is not None:
        sptpy = spotipy.Spotify(auth = token)
    sptpy.user_follow_artists(artists)

def unfollowArtist(artists, token = None, sptpy = None):
    if sptpy is None and token is not None:
        sptpy = spotipy.Spotify(auth = token)
    sptpy.user_unfollow_artists(artists)
