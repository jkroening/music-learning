######################
## take a spotify playlist and
## given a beginning song (artist name and title)
## output a playlist order based on
## echonest metadata similarity between songs
######################

import os
import sys
import requests
import time
import pandas as pd
import pdb
import shutil
from subprocess import call
from fuzzywuzzy import fuzz
from unidecode import unidecode
from sklearn import decomposition
from sklearn import preprocessing
from sklearn import cluster
import plotly.plotly as py
from plotly.graph_objs import *
import plotly.tools as tls
import numpy as np
sys.path.append( "../Modules")
import spotify_methods as sp
from db_methods import lookupSongBySpotifyID, lookupArtistBySpotifyID, saveDataFrame
from helpers import loadFile, callAPI

def pullEchoNestSong(api_key, track):
    url_base = "http://developer.echonest.com/api/v4/song/profile"
    
    track_id, spotify_uri = sp.getSpotifyTrackIDs(track)

    ## due to echonest using 2 different bucket params and url encoding the ampersand, payload cannot be used
    # payload = {'api_key' : api_key, 'track_id' : spotify_uri, 'bucket' : "audio_summary&bucket=id:spotify", 'format' : "json"}
    url_suffix = "?api_key=%s&track_id=%s&bucket=audio_summary&bucket=id:spotify&format=json" % (api_key, spotify_uri)
    url = url_base + url_suffix
    
    data = callAPI(url)

    ## if response is a success
    if int(data['response']['status']['code']) == 0:
        track = sp.pullSpotifyTrack(track_id)
        ## pop off unneeded data and flatten dict
        song = flattenDictCustom(data['response']['songs'][0])
        song.pop('audio_md5', None)
        song.pop('analysis_url', None)
        song['album'] = track['album']
        song['echonest_artist_id'] = song.pop('artist_id')
        if 'artist_foreign_ids' in song:
            song.pop('artist_foreign_ids')
        song['spotify_artist_id'] = track['spotify_artist_id']
        ## add spotify uri to song data
        song['spotify_id'] = track_id
        ## rename keys as necessary
        song['echonest_id'] = song.pop('id')
    elif int(data['response']['status']['code']) == 5:
        ## the song cannot be found by the spotify id
        track = sp.pullSpotifyTrack(track_id)
        url = "http://developer.echonest.com/api/v4/song/search"
        payload = {'api_key' : api_key, 'artist' : track['artist'], 'title' : track['title'], 'bucket' : "audio_summary", 'format' : "json"}
        data = callAPI(url, payload)
        ## pop off unneeded data and flatten dict
        song = flattenDictCustom(data['response']['songs'][0])
        ## check to be sure it's the correct song -- fuzzy string match of at least .75 levenshtein ratio
        if fuzz.ratio(song['title'].lower(), track['title'].lower()) >= 0.75 and fuzz.ratio(song['artist'].lower(), track['artist'].lower()) >= 0.90:
            song.pop('audio_md5', None)
            song.pop('analysis_url', None)
            song['album'] = track['album']
            song['echonest_artist_id'] = song.pop('artist_id')
            if 'artist_foreign_ids' in song:
                song.pop('artist_foreign_ids')
            song['spotify_artist_id'] = track['spotify_artist_id']
            ## add spotify uri to song data
            song['spotify_id'] = track_id
            ## rename keys as necessary
            song['echonest_id'] = song.pop('id')
        else:
            print "Song not found via EchoNest search."
            return None
    else:
        "Unrecognized error code."

    return song

def pullEchoNestArtistTerms(api_key, artist, related_artists = None, related_artist_index = 0, term_min = 0):
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

    data = callAPI(url, payload)

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

            spotify_data = callAPI(url)

            related_artists = spotify_data['artists']
            related_artist_id = {'spotify_artist_id' : sp.stripSpotifyURI(related_artists[0]['uri'])}
        else:
            related_artist_id = {'spotify_artist_id' : sp.stripSpotifyURI(related_artists[related_artist_index]['uri'])}

        return pullEchoNestArtistTerms(api_key, related_artist_id, related_artists, int(related_artist_index + 1), 3)

def getTermStats(term):
    term_freq = "%s_freq" % term['name'].replace(" ", "_")
    term_wt = "%s_wt" % term['name'].replace(" ", "_")
    freq = term['frequency']
    wt = term['weight']
    return term_freq, term_wt, freq, wt

def makeGenresDummies(artist):
    for genre in artist['genres']:
        artist[genre] = 1
    artist.pop('genres', None)
    return artist

def buildArtistDataFrame(tracks, song_db, artist_db, api_key):
    for track in tracks:
        track_id = sp.getSpotifyTrackIDs(track)[0]
        track_data = sp.pullSpotifyTrack(track_id)
        artist_id = track_data['spotify_artist_id']
        if not lookupArtistBySpotifyID(artist_id, artist_db):
            artist = sp.pullSpotifyArtist(artist_id)
            artist = makeGenresDummies(artist)
            artist_terms = pullEchoNestArtistTerms(api_key, artist)
            artist.update(artist_terms)
            artist_db.append(artist, ignore_index = True, inplace = True).fillna(0)
    return artist_db

def addArtistTermsToSongs(song_db, artist_db):
    db = pd.merge(song_db, artist_db, on = ['spotify_artist_id'])
    db = db.fillna(0)
    return db

def flattenDict(d):
    def expand(key, value):
        if isinstance(value, dict):
            return [ (key + '.' + k, v) for k, v in flattenDict(value).items() ]
        else:
            if isinstance(value, unicode):
                return [ (key, unidecode(value)) ]
            else:
                return [ (key, value) ]
    items = [ item for k, v in d.items() for item in expand(k, v) ]
    return dict(items)

def flattenDictCustom(d):
    """
    Custom function to flatten a dictionary but not label children keys by parent keys.
    """
    def expand(key, value):
        if isinstance(value, dict):
            return [ (k, v) for k, v in flattenDict(value).items() ]
        else:
            if isinstance(value, unicode):
                return [ (key, unidecode(value)) ]
            else:
                return [ (key, value) ]
    items = [ item for k, v in d.items() for item in expand(k, v) ]
    return dict(items)

def dataFrameToMatrix(df, cols_to_remove, substr_cols_to_remove):
    cols = df.columns.tolist()
    for col in cols_to_remove:
        cols.remove(col)
    for ss in substr_cols_to_remove:
        for c in cols:
            if ss in c:
                cols.remove(c)
    matrix = df[cols]
    return matrix

def transformPCA(X, n):
    pca = decomposition.PCA(n_components = n)
    X = pca.fit_transform(X)
    return X

def centerScaleData(X):
    standard_scaler = preprocessing.StandardScaler()
    X = standard_scaler.fit_transform(X)
    return X

def classifyUnsupervised(X, n_clusters = 6, method = "km", random_state = 42):
    if method == "km":
        clf = cluster.KMeans(init = "random", n_clusters = n_clusters, random_state = random_state)
        clusters = clf.fit_predict(X).tolist()
    return clusters

def scatterplot(data, filename, title = "", xAxisLabel = "", yAxisLabel = ""):
    trace1 = Scatter(
        x = data[ : , 0],
        y = data[ : , 1],
        mode = "markers"
    )
    layout = Layout(
        title = title,
        xaxis = XAxis(
            title = xAxisLabel,
            showgrid = False,
            zeroline = False
        ),
        yaxis = YAxis(
            title = yAxisLabel,
            showline = False
        )
    )
    data = Data([trace1])
    fig = Figure(data = data, layout = layout)
    plot_url = py.plot(fig, filename = filename)

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

def subsetDataFrame(df, tracks):
    ## subset dataframe by spotify ids
    track_ids = []
    for track in tracks:
        track_ids.append(sp.stripSpotifyLink(track))
    db_subset = df[df.spotify_id.isin(track_ids)]
    return db_subset

def closest(X, p):
    disp = X - p
    return np.argmin((disp * disp).sum(1))

def distances(X, p):
    disp = X - p
    return (disp * disp).sum(1)

## take pandas dataframe and reorder by distance from point p in distances()
def sortByDistance(df, dist):
    df = df.reset_index()
    return df.iloc[np.argsort(dist), ]

def writeIDsToURI(ids, location, filename):
    with open(os.path.join(location, filename), "w") as f:
        for i in ids:
            f.write("spotify:track:%s\n" % i)

def expandToPoints(X, df, artist, title):
    start = np.where((df.artist.str.lower() == artist.lower()) & (df.title.str.lower() == title.lower()))[0][0]
    ds = distances(X, X[start, : ])
    dfs = sortByDistance(df, ds)
    return dfs

def walkPoints(X, df, artist, title):
    try:
        start = np.where((df.artist.str.lower() == artist.lower()) & (df.title.str.lower() == title.lower()))[0][0]
    except:
        print "Artist name and Song title not found as entered..."
        print "Please try again."
        sys.exit()
    out_list = ["spotify:track:%s" % df.iloc[start].spotify_id]
    curr_point = X[start, : ].copy()
    ## once the point has been touched, make the value impossiblly far away
    X[start, : ] = np.repeat(10e9, X.shape[1])
    for i in xrange(X.shape[0] - 1):
        nxt = closest(X, curr_point)
        next_point = X[nxt, : ].copy()
        out_list.append("spotify:track:%s" % df.iloc[nxt].spotify_id)
        X[nxt, : ] = np.repeat(10e9, X.shape[1])
        curr_point = next_point
    return out_list

def getSimilarPoints(X, df, artist, title):
    dfs = expandToPoints(X, df, artist, title)
    neighbors = dfs[1:6][['artist', 'title']]
    print neighbors

def writeTextFile(data, location, filename):
    with open(os.path.join(location, filename), "w") as f:
        for line in data:
            f.write("%s\n" % line)

def main():

    ## set echonest API key
    config = loadFile("../config", "config.csv", True)
    api_key = config['ECHONEST_API_KEY']
    ## set plotly API key
    plotly_username = config['PLOTLY_USERNAME']
    plotly_api_key = config['PLOTLY_API_KEY']
    plotly_stream_ids = config['PLOTLY_STREAM_IDS']
    tls.set_credentials_file(username=plotly_username, api_key=plotly_api_key, stream_ids=plotly_stream_ids)

    # ## load tracks in playlist
    in_tracks = loadFile("input", "input.txt")
    
    ## load database of metadata
    echonest_song_db = loadFile("../Databases", "echonest_song_db.csv")
    shutil.copyfile("../Databases/echonest_song_db.csv", "../Databases/_Backup/echonest_song_db.csv")
    echonest_artist_db = loadFile("../Databases", "echonest_artist_db.csv")
    shutil.copyfile("../Databases/echonest_artist_db.csv", "../Databases/_Backup/echonest_artist_db.csv")

    for track in in_tracks:
        if not lookupSongBySpotifyID(track, echonest_song_db):
            song = pullEchoNestSong(api_key, track)
            if song is not None:
                echonest_song_db = echonest_song_db.append(song, ignore_index = True)
            else:
                print "{} not found.".format(track)
    saveDataFrame(echonest_song_db, "../Databases", "echonest_song_db.csv")

    ## subset song database on tracks in playlist
    db_subset = subsetDataFrame(echonest_song_db, in_tracks)

    ## if user wants to use terms to cluster songs in walk, then third passed argument should be "terms"
    if len(sys.argv) > 1 and sys.argv[1] == "terms":
        ## build dict of artists with echonest terms
        artist_db = buildArtistDataFrame(in_tracks, echonest_song_db, echonest_artist_db, api_key)
        saveDataFrame(artist_db, "../Databases", "echonest_artist_db.csv")

        ## add artist terms to songs subset db
        artist_db = artist_db.drop('artist', 1) ## because capitalization might be different, drop 'artist' from one of the dataframes before merging
        db = addArtistTermsToSongs(db_subset, artist_db)
    else:
        db = db_subset

    cols_to_remove = ["spotify_id", "echonest_id", "title", "album", "artist", "echonest_artist_id", "spotify_artist_id", "duration", "time_signature", "key", "mode", "loudness"]
    substr_cols_to_remove = ["_freqwt", "_freq"]  ## "_freqwt" is overkill for the sake of explicitness, as "_freq" is in "_freqwt"
    X = dataFrameToMatrix(db, cols_to_remove, substr_cols_to_remove)

    X = X.fillna(0)
    X = centerScaleData(X)

    ## create directed walk starting at song from sys args
    artist = raw_input('Enter artist name: ')
    song = raw_input('Enter song name: ')

    neighbors = getSimilarPoints(X.copy(), db_subset, artist, song)


if __name__ == "__main__":
    main()