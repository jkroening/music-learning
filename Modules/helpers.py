import os
import time
import csv
import re
import requests
import shutil
import itertools
import pdb
import numpy as np
import pandas as pd
from unidecode import unidecode
import data_methods as dam
import spotify_methods as sptfy
import db_methods as dbm
import module_helpers as mhlpr

def loadFile(location, filename, as_dict = False):
    try:
        with open(os.path.join(location, filename), "U") as f:
            if ".json" in filename:
                infile = json.load(f)
            elif ".csv" in filename and not as_dict:
                infile = pd.io.parsers.read_csv(f)
            elif ".csv" in filename and as_dict:
                reader = csv.reader(f)
                infile = {}
                for row in reader:
                    infile[row[0]] = row[1]
            elif ".txt" in filename:
                infile = f.read().splitlines()
            else:
                infile = f.read()
    except Exception as e:
        print(e)
        if ".json" in filename:
            infile = {}
        elif ".csv" in filename:
            infile = pd.DataFrame(index = None, columns = None)
        elif ".txt" in filename:
            infile = []
        else:
            infile = None
    return infile

def writeTextFile(data, location, filename):
    with open(os.path.join(location, filename), "w") as f:
        for line in data:
            f.write("%s\n" % line)

def loadPlotly():
    config = loadFile("../config", "config.csv", True)
    ## set plotly API key
    plotly_username = config['PLOTLY_USERNAME']
    plotly_api_key = config['PLOTLY_API_KEY']
    plotly_stream_ids = config['PLOTLY_STREAM_IDS']
    plt.set_credentials_file(
        username=plotly_username
        , api_key=plotly_api_key
        , stream_ids=plotly_stream_ids
    )
    return plt

def dataFrameToMatrix(df, cols_to_remove = [], substr_cols_to_remove = [], cols_to_keep = [], fillNA = True, centerScale = True):
    if not len(cols_to_keep):
        cols = df.columns.tolist()
        for col in cols_to_remove:
            cols.remove(col)
        for ss in substr_cols_to_remove:
            for c in cols:
                if ss in c:
                    cols.remove(c)
    else:
        cols = cols_to_keep
    matrix = df[cols]
    if fillNA:
        matrix = matrix.fillna(0)
    if centerScale:
        matrix = dam.centerScaleData(matrix)
    return matrix

def separateMatrixClusters(X, clusters):
    ## reshape clusters
    clust = np.reshape(np.array(clusters), (1, -1)).T
    A = np.append(X, clust, 1)
    cluster_groups = []
    for i in xrange(max(clusters) + 1):
        cl = A[np.where(A[ : , -1] == i)]
        cluster_groups.append(cl)
    return cluster_groups

def separateDataFrameClusters(df, clusters):
    df.loc[ : , 'cluster'] = pd.Series(clusters, index = df.index)
    cluster_groups = []
    for i in xrange(max(clusters) + 1):
        cl = df[df.cluster == i]
        cluster_groups.append(cl)
    return cluster_groups

def parseLocalTrackURL(track):
    artist = track.split("/")[-4]
    track = track.split("/")[-2].replace("%20", " ")
    return artist, track

def chooseTrack(db, songs, missings, ids, playlist, artist, title, song, i, query = 'Select next song (enter number): '):
    pd.set_option('display.max_rows', 100)
    if not songs.empty:
        songs.index = np.arange(1, len(songs) + 1)
        print("\n", songs[["title", "artist"]].to_string(), "\n")
    else:
        print("")
    if len(missings) > 0:
        j = len(songs) + 1
        k = len(songs) + len(missings) + 1
        missings_index = np.arange(j, k)
        print("Songs without metadata:\n") ## do not have neighbors
        new_missings = []
        for idx, missing_track in zip(missings_index, missings):
            if 'spotify.com' in missing_track:
                a, t = parseLocalTrackURL(missing_track)
            else:
                a = missing_track[0]
                t = missing_track[1]
            new_missings.append((a, t))
            print(idx, "\t", a, "\t", t)
        missings = new_missings
        print("\n")
    else:
        k = len(songs) + 1
    selection = int(input(query))
    while selection not in np.arange(1, k):
        selection = int(input(query))
    if len(missings) > 0:
        if selection in np.arange(j, k):
            ids.append(selection)
            a = np.array(missings)[missings_index == selection][0][0]
            t = np.array(missings)[missings_index == selection][0][1]
            song = selection
            artist = a
            title = t
            missings = np.array(missings)[missings_index != selection].tolist()
        else:
            ids.append(songs.spotify_id[selection])
            a = songs.artist[selection]
            t = songs.title[selection]
            song = checkTrackIndex(db, songs, selection)
            artist = db.artist[song]
            title = db.title[song]
    else:
        ids.append(songs.spotify_id[selection])
        a = songs.artist[selection]
        t = songs.title[selection]
        song = checkTrackIndex(db, songs, selection)
        artist = db.artist[song]
        title = db.title[song]
    if i < 10:
        playlist.append("{}.  {} - {}".format(i, a, t))
    else:
        playlist.append("{}. {} - {}".format(i, a, t))
    print("\nYou just chose: {} - {}".format(a, t))
    return songs, missings, ids, playlist, artist, title, song

def checkTrackIndex(db, songs, selection):
    spotify_id = songs.spotify_id[selection]
    echonest_id = songs.echonest_id[selection]
    title = songs.title[selection]
    song = np.bincount(np.concatenate(
        (db.index[db.spotify_id == spotify_id].values,
         db.index[db.title == title].values)
    )).argmax()
    return song

def processInput(terms = False, genres = False, input_playlist = None, token = None):
    ## set spotify auth
    config = loadFile("../config", "config.csv", True)
    if token is not None:
        sptpy = sptfy.Spotify(auth = token)
    sptpy = sptfy.getSpotifyCred()

    ## load tracks in playlist
    if input_playlist is not None:
        in_tracks = loadFile("../input", input_playlist)
    else:
        in_tracks = loadFile("../input", "input.txt")

    ## load database of metadata
    song_db = loadFile("../Databases", "song_db.csv")
    shutil.copyfile("../Databases/song_db.csv",
                    "../Databases/_Backup/song_db.csv")
    artist_db = loadFile("../Databases", "artist_db.csv")
    shutil.copyfile("../Databases/artist_db.csv",
                    "../Databases/_Backup/artist_db.csv")

    unfound_tracks = []
    for track in in_tracks:
        if 'local' in track:
            artist, title, album = sptfy.formatLocalTrack(track)
            song_uri = sptfy.searchSpotifyTrack(
                artist,
                title,
                album,
                first = True,
                token = token,
                sptpy = sptpy
            )
            if song_uri is not None:
                if not dbm.lookupSongBySpotifyID(song_uri, song_db):
                    song = sptfy.getAudioFeatures(song_uri, token = token, sptpy = sptpy)
                    if song is not None:
                        song_db = song_db.append(song, ignore_index = True)
            else:
                print("{} not found.".format(track))
                unfound_tracks.append(track)
        else:
            if not dbm.lookupSongBySpotifyID(track, song_db):
                song = sptfy.getAudioFeatures(track, token = token, sptpy = sptpy)
                if song is not None:
                    song_db = song_db.append(song, ignore_index = True)
                else:
                    print("{} not found.".format(track))
                    unfound_tracks.append(track)
    song_db = song_db.drop_duplicates('spotify_id')
    dbm.saveDataFrame(song_db, "../Databases", "song_db.csv")

    ## subset song database on tracks in playlist
    db_subset = dbm.subsetDataFrame(song_db, in_tracks)

    if genres:
        ## build dict of artists with genres
        artist_db = dbm.buildArtistDataFrame(
            db_subset,
            artist_db,
            token = token,
            sptpy = sptpy
        )
        dbm.saveDataFrame(artist_db, "../Databases", "artist_db.csv")

        ## add artist genres to songs subset db
        ## and because capitalization might be different
        ## drop 'artist' from one of the dataframes before merging
        artist_db = artist_db.drop('artist', 1)
        db_out = dbm.addArtistDataToSongs(db_subset, artist_db)
    else:
        db_out = db_subset

    return db_out, unfound_tracks

def sortGenres(artist_name, artist_id, track_name, track_id, secondary_artist,
               token = None, sptpy = None, makePlaylists = False):
    ## we load the genres inside the function because they can be appended to
    ## below if a new genre presents itself for classification
    genre_db = dbm.buildSubgenres()
    for k, v in genre_db.items():
        genre_db[k] = mhlpr.flattenDictCustom(v).keys()
    all_genres = [v for k, v in genre_db.items() for v in genre_db[k]]
    genres = sptfy.getArtistGenres(artist_id, token = token, sptpy = sptpy)
    electronic = genre_db['electronic']
    indie = genre_db['indie']
    pop = genre_db['pop']
    poprock = genre_db['poprock']
    rock = genre_db['rock']
    urban = genre_db['urban']
    if len(genres) < 1 and makePlaylists:
        with open('../output/unknowntracks.txt', 'a+') as f:
            f.write('spotify:track:%s\r' % track_id)
            print("Not found: {} - {}".format(artist_name, track_name))
    else:
        e, i, p, o, u, r = [0] * 6
        for g in genres:
            g = re.sub(r"[^a-zA-Z0-9]", '_', g)
            if g in electronic:
                e = e + 1
            if g in indie:
                i = i + 1
            if g in pop:
                p = p + 1
            if g in poprock:
                o = o + 1
            if g in urban:
                u = u + 1
            if g in rock:
                r = r + 1
            if g not in all_genres:
                user_input = [None]
                while not os.path.isfile("../Databases/genres/{}.txt".format(user_input[0])):
                    user_input = input(
                        '\nIn which genre group(s) does {} belong? [{}] (separate by space)\
                        \nelectronic \
                        \nindie \
                        \npop \
                        \npoprock \
                        \nrock \
                        \nurban\n\n'.format(g, artist_name)
                    ).split()
                for ui in user_input:
                    with open("../Databases/genres/{}.txt".format(ui), "a") as f:
                        f.write(g + "\n")
                    all_genres.append(g)
                    if ui == "electronic":
                        e = e + 1
                    if ui == "indie":
                        i = i + 1
                    if ui == "pop":
                        p = p + 1
                    if ui == "poprock":
                        o = o + 1
                    if ui == "urban":
                        u = u + 1
                    if ui == "rock":
                        r = r + 1
        scores = {"electronic" : e, "indie" : i, "pop" : p,
                  "poprock" : o, "urban" : u, "rock" : r}
        if sum(scores.values()) == 0:
            maxes = []
        else:
            maxes = [k for k, v in scores.items() if v == max(scores.values())]
        if secondary_artist is not None and len(maxes) > 0 and 'pop' not in maxes:
            ## use featuring artist genres too
            genres = genres + sptfy.getArtistGenres(secondary_artist, token = token, sptpy = sptpy)
            e, i, p, o, u, r = [0] * 6
            for g in genres:
                g = re.sub(r"[^a-zA-Z0-9]", '_', g)
                if g in electronic:
                    e = e + 1
                if g in indie:
                    i = i + 1
                if g in pop:
                    p = p + 1
                if g in poprock:
                    o = o + 1
                if g in urban:
                    u = u + 1
                if g in rock:
                    r = r + 1
                if g not in all_genres:
                    user_input = [None]
                    while not os.path.isfile("../Databases/genres/{}.txt".format(user_input[0])):
                        user_input = input(
                            '\nIn which genre group(s) does {} belong? [{}] (separate by space)\
                            \nelectronic \
                            \nindie \
                            \npop \
                            \npoprock \
                            \nrock \
                            \nurban\n\n'.format(g, artist_name)
                        ).split()
                    for ui in user_input:
                        with open("../Databases/genres/{}.txt".format(ui), "a") as f:
                            f.write(g + "\n")
                        all_genres.append(g)
                        if ui == "electronic":
                            e = e + 1
                        if ui == "indie":
                            i = i + 1
                        if ui == "pop":
                            p = p + 1
                        if ui == "poprock":
                            o = o + 1
                        if ui == "urban":
                            u = u + 1
                        if ui == "rock":
                            r = r + 1
            scores = {"electronic" : e, "indie" : i, "pop" : p,
                      "poprock" : o, "urban" : u, "rock" : r}
            maxes = [k for k, v in scores.items() if v == max(scores.values())]
        if artist_name in ["Radiohead"]:
            pdb.set_trace()
        if len(maxes) == 1 or ('pop' in maxes and 'electronic' in maxes):
            with open(os.path.join("../output/", maxes[0] + "tracks.txt"), "a+") as f:
                f.write('spotify:track:%s\r' % track_id)
        else:
            # if there are ties, this takes the first genre listed of the ties
            for m in maxes:
                g = re.sub(r"[^a-zA-Z0-9]", '_', genres[0])
                if g in genre_db[m]:
                    with open(os.path.join("../output/", m + "tracks.txt"), "a+") as f:
                        f.write('spotify:track:%s\r' % track_id)
                    break
