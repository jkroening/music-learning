from helpers import callAPI
from unidecode import unidecode

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
    track_data = {'title' : song, 'album' : album, 'artist_name' : artist, 'spotify_artist_id' : artist_id, 'spotify_album_id' : album_id, 'popularity' : data['popularity']}
    return track_data

def pullSpotifyArtist(artist_id):
    url = "https://api.spotify.com/v1/artists/%s" % artist_id.strip()
    data = callAPI(url)
    genres = data['genres']
    name = data['name']
    popularity = data['popularity']
    artist_data = {'artist_name' : name, 'spotify_artist_id' : artist_id, 'genres' : genres, 'artist_popularity' : popularity}
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
    album_data = {'album_name' : album_name, 'artist_name' : artist, 'spotify_artist_id' : artist_id, 'release_date' : release_date, 'year' : year}
    return album_data

def stripSpotifyLink(http_link):
    spotify_id = str(http_link).replace("https://open.spotify.com/track/", "").strip()
    return spotify_id

def stripSpotifyURI(uri):
    spotify_id = str(uri).split(":")[-1]
    return spotify_id