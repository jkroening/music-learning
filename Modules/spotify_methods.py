from helpers import callAPI
from unidecode import unidecode
from flask import Flask, redirect, url_for, session, request
from flask_oauthlib.client import OAuth, OAuthException
import urllib2

def authSpotify(config):
    SPOTIFY_APP_ID = config['SPOTIFY_APP_ID']
    SPOTIFY_APP_SECRET = config['SPOTIFY_APP_SECRET']

    app = Flask(__name__)
    app.debug = True
    app.secret_key = 'development'
    oauth = OAuth(app)

    spotify = oauth.remote_app(
        'spotify',
        consumer_key = SPOTIFY_APP_ID,
        consumer_secret = SPOTIFY_APP_SECRET,
        # Change the scope to match whatever it us you need
        # list of scopes can be found in the url below
        # https://developer.spotify.com/web-api/using-scopes/
        request_token_params = {'scope': 'playlist-read-private'},
        base_url = 'https://accounts.spotify.com',
        request_token_url = None,
        access_token_url = '/api/token',
        authorize_url = 'https://accounts.spotify.com/authorize'
    )

    @app.route('/')
    def index():
        return redirect(url_for('login'))

    @app.route('/login')
    def login():
        callback = url_for(
            'spotify_authorized',
            next = request.args.get('next') or request.referrer or None,
            _external = True
        )
        return spotify.authorize(callback = callback)

    @app.route('/login/authorized')
    def spotify_authorized():
        resp = spotify.authorized_response()
        if resp is None:
            return 'Access denied: reason={0} error={1}'.format(
                request.args['error_reason'],
                request.args['error_description']
            )
        if isinstance(resp, OAuthException):
            return 'Access denied: {0}'.format(resp.message)

        session['oauth_token'] = (resp['access_token'], '')
        me = spotify.get('/me')
        return 'Logged in as id={0} name={1} redirect={2}'.format(
            me.data['id'],
            me.data['name'],
            request.args.get('next')
        )

    @spotify.tokengetter
    def get_spotify_oauth_token():
        return session.get('oauth_token')

    return app

def getSpotifyTrackIDs(text):
    if "spotify:track:" in text:
        track_id = stripSpotifyURI(text)
        spotify_uri = track
    else:
        track_id = stripSpotifyLink(text)
        spotify_uri = "spotify:track:%s" % track_id
    return track_id, spotify_uri

def getSpotifyArtistIDs(text):
    if "spotify:artist:" in text:
        artist_id = stripSpotifyURI(text)
        spotify_uri = track
    else:
        artist_id = stripSpotifyLink(text)
        spotify_uri = "spotify:artist:%s" % artist_id
    return artist_id, spotify_uri

def getSpotifyAlbumIDs(text):
    if "spotify:album:" in text:
        album_id = stripSpotifyURI(text)
        spotify_uri = track
    else:
        album_id = stripSpotifyLink(text)
        spotify_uri = "spotify:album:%s" % album_id
    return album_id, spotify_uri

def pullSpotifyTrack(track_id):
    url = "https://api.spotify.com/v1/tracks/%s" % track_id.strip()
    data = callAPI(url)
    song = unidecode(data['name'])
    album = unidecode(data['album']['name'])
    artist = unidecode(data['artists'][0]['name'])
    artist_id = stripSpotifyURI(data['artists'][0]['uri'])
    album_id = stripSpotifyURI(data['album']['uri'])
    track_data = {'title' : song, 'album' : album, 'spotify_id' : track_id, 'artist' : artist, 'spotify_artist_id' : artist_id, 'spotify_album_id' : album_id, 'popularity' : data['popularity']}
    return track_data

def pullSpotifyArtist(artist_id):
    url = "https://api.spotify.com/v1/artists/%s" % artist_id.strip()
    data = callAPI(url)
    genres = data['genres']
    name = data['name']
    popularity = data['popularity']
    artist_data = {'artist' : name, 'spotify_artist_id' : artist_id, 'genres' : genres, 'artist_popularity' : popularity}
    return artist_data

def pullSpotifyAlbum(album_id):
    url = "https://api.spotify.com/v1/albums/%s" % album_id.strip()
    data = callAPI(url)
    album_name = unidecode(data['name'])
    artist = unidecode(data['artists'][0]['name'])
    artist_id = stripSpotifyURI(data['artists'][0]['uri'])
    release_date = data['release_date']
    if data['release_date_precision'] == 'day':
        year = release_date[0:4]
    elif data['release_date_precision'] == 'year':
        year = release_date
    album_data = {'album_name' : album_name, 'artist' : artist, 'spotify_artist_id' : artist_id, 'release_date' : release_date, 'year' : year}
    return album_data

def searchSpotifyTrack(artist, title, album = None):
    url = "https://api.spotify.com/v1/search"
    payload = {'q' : [artist, title, album], 'type': "track", 'limit' : 50, 'market' : "US"}
    data = callAPI(url, payload)
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
    return tracks

def stripSpotifyLink(http_link):
    if 'local' in http_link:
        return http_link.strip()
    else:
        spotify_id = str(http_link).replace("https://open.spotify.com/track/", "").strip()
        return spotify_id

def stripSpotifyURI(uri):
    spotify_id = str(uri).split(":")[-1]
    return spotify_id

def formatLocalTrack(link):
    s = link.split("local/")[1]
    artist = urllib2.unquote(s.split("/")[0])
    title = urllib2.unquote(s.split("/")[2])
    album = urllib2.unquote(s.split("/")[1])
    return artist, title, album




