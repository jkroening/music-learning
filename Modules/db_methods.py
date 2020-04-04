import os
import re
import pdb
import itertools
import pandas as pd
import spotify_methods as sptfy
import module_helpers as mhlpr

def lookupSongBySpotifyID(song, df):
    track_id = sptfy.getSpotifyTrackIDs(song)[0]
    return any(df.spotify_id == track_id)

def lookupArtistBySpotifyID(artist, df):
    artist_id = sptfy.getSpotifyArtistIDs(artist)[0]
    idxs = df[df.spotify_artist_id == artist_id].index
    return any(df.spotify_artist_id == artist_id), idxs

def lookupAlbumBySpotifyID(album, df):
    album_id = sptfy.getSpotifyAlbumIDs(album)[0]
    return any(df.spotify_album_id == album_id)

def lookupSongByEchoNestID(song_id, df):
    return any(df.echonest_id == song_id)

def lookupAlbumByArtist(artist, album, df):
    return any(df.artist == artist) and any(df.album == album)

def saveDataFrame(df, location, filename):
    # dataframe to csv
    with open(os.path.join(location, filename), "w") as f:
         df.to_csv(f, index = False, index_label = False, encoding = "utf-8")

def subsetDataFrame(df, tracks):
    ## subset dataframe by spotify ids
    track_ids = []
    for track in tracks:
        track_ids.append(sptfy.getSpotifyTrackIDs(track)[0])
    db_subset = df[df.spotify_id.isin(track_ids)]
    return db_subset

def makeGenresDummies(artist, album = None):
    for genre in artist['genres']:
        artist[re.sub("[\W\d]", "_", genre.strip())] = 1
    if album is not None:
        for genre in album['genres']:
            if re.sub("[\W\d]", "_", genre.strip()) not in artist:
                artist[re.sub("[\W\d]", "_", genre.strip())] = 1
    artist.pop('genres', None)
    return artist

def buildArtistDict(tracks):
    # get all unique artist uris
    artists = {}
    for i, r in tracks.iterrows():
        artists[r['artist_id']] = {'artist' : r['artist_name']}
    return artists

def buildArtistDataFrame(song_db, artist_db, token = None):
    for i, row in song_db.iterrows():
        ## also check if no subgenres are marked (ie. all are zero) and if so
        ## check again
        exists, idxs = lookupArtistBySpotifyID(row.spotify_artist_id, artist_db)
        genres_sum = 0
        flat_genres = mhlpr.flattenDictCustom(buildSubgenres()).keys()
        if exists:
            match = artist_db[artist_db.spotify_artist_id == row.spotify_artist_id]
            matching_cols = [col for col in match.columns.values if col in flat_genres]
            match_subset = match[matching_cols].squeeze()
            match_genres = match_subset[match_subset.values != 0].index
            genres_sum = sum(match_subset)
        if genres_sum == 0:
            try:
                artist = sptfy.pullSpotifyArtist(row.spotify_artist_id, token = token)
                album = sptfy.pullSpotifyAlbum(row.spotify_album_id, token = token)
            except:
                return artist_db
            gs = set(artist['genres'] + album['genres'])
            gs = [re.sub(r"[^a-zA-Z0-9]", '_', x) for x in gs]
            new_genres = set(gs).difference(set(flat_genres))
            artist = makeGenresDummies(artist, album)
            if len(new_genres) > 0:
                for g in new_genres:
                    user_input = [None]
                    while not os.path.isfile("../Databases/genres/{}.txt".format(user_input[0])):
                        user_input = raw_input(
                            '\nIn which genre group(s) does {} belong? [{}] (separate by space)\
                            \nelectronic \
                            \nindie \
                            \npop \
                            \npoprock \
                            \nrock \
                            \nurban\n\n'.format(g, artist['artist'].encode('utf-8').strip())
                        ).split()
                    for ui in user_input:
                        with open("../Databases/genres/{}.txt".format(ui), "a") as f:
                            f.write(g + "\n")
                        if "ALL.{}".format(ui) in artist:
                            artist["ALL.{}".format(ui)] += 1
                        else:
                            artist["ALL.{}".format(ui)] = 1
            ## reload genres since new_genres were just added
            genres = buildSubgenres()
            for g in set(gs).difference(new_genres):
                for k, v in genres.items():
                    if g in v:
                        if "ALL.{}".format(k) in artist:
                            artist["ALL.{}".format(k)] += 1
                        else:
                            artist["ALL.{}".format(k)] = 1
            artist.pop('artist_popularity', None)
            if exists:
                artist_db.update(pd.DataFrame(artist, index = idxs))
            else:
                artist_db = artist_db.append(artist, ignore_index = True).fillna(0)
    return artist_db

def addArtistDataToSongs(song_db, artist_db):
    db = pd.merge(song_db, artist_db, on = ['spotify_artist_id'])
    db = db.fillna(0)
    return db

def buildSubgenres():
    electronic = map(str.lower, open('../Databases/genres/electronic.txt').read().splitlines())
    electronic = [re.sub(r"[^a-zA-Z0-9]", '_', x) for x in electronic]
    indie = map(str.lower, open('../Databases/genres/indie.txt').read().splitlines())
    indie = [re.sub(r"[^a-zA-Z0-9]", '_', x) for x in indie]
    pop = map(str.lower, open('../Databases/genres/pop.txt').read().splitlines())
    pop = [re.sub(r"[^a-zA-Z0-9]", '_', x) for x in pop]
    poprock = map(str.lower, open('../Databases/genres/poprock.txt').read().splitlines())
    poprock = [re.sub(r"[^a-zA-Z0-9]", '_', x) for x in poprock]
    rock = map(str.lower, open('../Databases/genres/rock.txt').read().splitlines())
    rock = [re.sub(r"[^a-zA-Z0-9]", '_', x) for x in rock]
    urban = map(str.lower, open('../Databases/genres/urban.txt').read().splitlines())
    urban = [re.sub(r"[^a-zA-Z0-9]", '_', x) for x in urban]
    return {
        'electronic' : dict(zip(electronic, itertools.cycle([0]))),
        'indie' : dict(zip(indie, itertools.cycle([0]))),
        'pop' : dict(zip(pop, itertools.cycle([0]))),
        'poprock' : dict(zip(poprock, itertools.cycle([0]))),
        'rock' : dict(zip(rock, itertools.cycle([0]))),
        'urban' : dict(zip(urban, itertools.cycle([0])))
    }
