import os
import spotify_methods as sp

def lookupSongBySpotifyID(song, df):
    track_id = sp.getSpotifyTrackIDs(song)[0]
    return any(df.spotify_id == track_id)

def lookupArtistBySpotifyID(artist, df):
    artist_id = sp.getSpotifyArtistIDs(artist)[0]
    return any(df.spotify_artist_id == artist_id)

def lookupAlbumBySpotifyID(album, df):
    album_id = sp.getSpotifyAlbumIDs(album)[0]
    return any(df.spotify_album_id == album_id)

def lookupAlbumByArtist(artist, album, df):
    return any(df.artist == artist) and any(df.album == album)

def saveDataFrame(df, location, filename):
    # dataframe to csv
    with open(os.path.join(location, filename), "w") as f:
         df.to_csv(f, index = False, index_label = False, encoding = "utf-8")