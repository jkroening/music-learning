######################
## given an input of spotify playlists
## cluster all the songs by echonest term similarity
## and output into separate playlists
######################

import os
import sys
import pdb
import requests
import time
import json
import pandas as pd
from sklearn import cluster
from sklearn import neighbors
from sklearn import decomposition
import matplotlib.pyplot as plt
from django.utils.encoding import smart_str, smart_unicode
import shutil
from unidecode import unidecode
sys.path.append( "../Modules")
from helpers import loadFile


def loadFile(filename):
    data = []
    with open(filename) as f:
        data = f.read().splitlines()
    return data

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

def stripSpotifyLink(http_link):
    spotify_id = str(http_link).replace("https://open.spotify.com/track/", "")
    return spotify_id

def stripSpotifyURI(uri):
    spotify_id = str(uri).split(":")[-1]
    return spotify_id

def spotifyTrackLookup(track_id):
    url = "https://api.spotify.com/v1/tracks/%s" % track_id.strip()
    data = callAPI(url, None)
    track_title = smart_str(data['name'])
    album_title = smart_str(data['album']['name'])
    artist = smart_str(data['artists'][0]['name'])
    artist_id = stripSpotifyURI(data['artists'][0]['uri'])
    track_data = {'track_title' : track_title, 'album_title' : album_title, 'artist' : artist, 'artist_id' : artist_id, 'popularity' : data['popularity']}
    return track_data

def buildArtistDict(tracks):
    # get all unique artist uris
    artists = {}
    for r in tracks.iterrows():
        artists[r[1]['artist_id']] = {'artist' : r[1]['artist']}
    return artists

def getTermStats(term):
    term_freq = "%s_freq" % term['name'].replace(" ", "_")
    term_wt = "%s_wt" % term['name'].replace(" ", "_")
    freq = term['frequency']
    wt = term['weight']
    return term_freq, term_wt, freq, wt

def echoNestTermLookup(api_key, artists, artist_archive, cluster_df, update = False):
    for artist_id in artists:
        # if already have artist data from previous runs and update is False, then get data from artist_archive and skip lookup
        if artist_id in artist_archive and not update:
            artists[artist_id].update(artist_archive[artist_id])
        else:
            url = "http://developer.echonest.com/api/v4/artist/terms"
            spotify_uri = "spotify:artist:%s" % artist_id
            payload = {'api_key' : api_key, 'id' : spotify_uri, 'format' : "json"}
            data = callAPI(url, payload)
            # get terms from json
            terms = data['response']['terms']
            if len(terms) > 0:
                for term in terms:
                    term_freq, term_wt, freq, wt = getTermStats(term)
                    # # frequence and weight as metric
                    # artists[artist_id][term_freq] = freq
                    # artists[artist_id][term_wt] = wt
                    # # frequency * weight as metric
                    # artists[artist_id][term_wt] = freq * wt
                    # just weight as metric
                    artists[artist_id][term_wt] = wt
            else:
                # there are no terms for this artist
                # so search for related artists and get their terms
                url = "https://api.spotify.com/v1/artists/%s/related-artists" % artist_id
                spotify_data = callAPI(url, None)
                terms = []
                i = 0
                # check to find a related artist with at least 3 terms
                while len(terms) < 3:
                    if i >= len(spotify_data['artists']):
                        i = 0
                        related_artist_id = stripSpotifyURI(spotify_data['artists'][i]['uri'])
                        url = "http://developer.echonest.com/api/v4/artist/terms"
                        spotify_uri = "spotify:artist:%s" % related_artist_id
                        payload = {'api_key' : api_key, 'id' : spotify_uri, 'format' : "json"}
                        data = callAPI(url, payload)
                        terms = data['response']['terms']
                        break
                    related_artist_id = stripSpotifyURI(spotify_data['artists'][i]['uri'])
                    url = "http://developer.echonest.com/api/v4/artist/terms"
                    spotify_uri = "spotify:artist:%s" % related_artist_id
                    payload = {'api_key' : api_key, 'id' : spotify_uri, 'format' : "json"}
                    data = callAPI(url, payload)
                    terms = data['response']['terms']
                    i += 1
                for term in terms:
                    term_freq, term_wt, freq, wt = getTermStats(term)
                    # # frequence and weight as metric
                    # artists[artist_id][term_freq] = freq
                    # artists[artist_id][term_wt] = wt
                    # # frequency * weight as metric
                    # artists[artist_id][term_wt] = freq * wt
                    # just weight as metric
                    artists[artist_id][term_wt] = wt
        # assign -1 as playlist_id for artists with no cluster assignment yet
        if artist_id in cluster_df.index:
            artists[artist_id]['playlist_id'] = cluster_df.loc[artist_id, "playlist_id"]
        else:
            artists[artist_id]['playlist_id'] = -1
    # merge the two dictionaries, overwriting artist_archive with any updates from artists
    out_artists = artist_archive.copy()
    out_artists.update(artists)
    return out_artists

def sortTuple(tracks, reverse = False):
    sorted_tuple = sorted(tracks, key = lambda x: x[1], reverse = reverse)
    return sorted_tuple

def writeToFile(tracks, out_filename):
    with open(out_filename, 'w') as f:
        f.write('%s\n' % tracks[0])


def main():

    # the number of playlists to output
    # if this number has changed since a previous run, knn (supervised learning) cannot be used
    # as the cluster centers will be different due to this different k. this is prompted below.
    n_playlists = int(sys.argv[1])

    # update artist_archive terms
    update = False

    # load artist archive json
    try:
        with open("data/artist_archive.json") as f:
            artist_archive = json.load(f)
    except:
        artist_archive = {}
    # load track archive json
    try:
        with open("data/track_archive.json") as f:
            tracks = json.load(f)
            tracks = pd.DataFrame(tracks)
    except:
        tracks = pd.DataFrame(index = None, columns = ['album_title', 'artist_id', 'artist', 'playlist_id', 'popularity', 'track_title'])

    # load the playlists to cluster
    playlist_locs = sys.argv[2:]
    for p in playlist_locs:
        playlist = loadFile(p)
        for http_link in playlist:
            track_id = stripSpotifyLink(http_link)
            # no duplicates
            if track_id not in tracks.index:
                # build tracks dict
                out = spotifyTrackLookup(track_id)
                tracks.loc[track_id] = [out.album_title, out.artist_id, out.artist, -1, out.popularity, out.track_title]

    # load playlist assignments
    try:
        path = "playlists"
        cluster_df = pd.DataFrame(index = None, columns = ["artist", "playlist_id"])
        n = 0
        for filename in os.listdir(path):
            if filename.endswith(".txt"):
                with open(os.path.join(path, filename), 'U') as f:
                    for line in f.readlines():
                        artist_id = line.split(", ")[0]
                        artist = line.split(", ")[1].strip()
                        cluster_df.loc[artist_id] = [artist, n]
                    n += 1
        # with open("data/clusters.csv") as f:
        #     cluster_df = pd.io.parsers.read_csv(f, index_col = "artist_id")
    except:
        cluster_df = pd.DataFrame(index = None, columns = None)

    # build dict of artists to lookup terms for
    artists = buildArtistDict(tracks, culster)

    # get terms for artists
    config = loadFile("../config", "config.csv", True)
    api_key = config['ECHONEST_API_KEY']
    artists = echoNestTermLookup(api_key, artists, artist_archive, cluster_df, update)

    # with NAs to 0
    artists_df = pd.DataFrame(artists).T.fillna(0)
    artists_X = artists_df
    # split df into train and prediction set
    # may need to implement cross-val at some point
    cols = artists_X.columns.tolist()
    cols.remove('playlist_id')
    cols.remove('artist')
    artists_train = artists_X[artists_X.playlist_id != -1][cols] # where playlist_id != -1, and then exclude playlist_id column from assignment
    artists_predict = artists_X[artists_X.playlist_id == -1][cols] # where playlist_id == -1, and then exclude playlist_id column from assignment
    Y_train = artists_X[artists_X.playlist_id != -1]['playlist_id'].values
    # drop columns not used in analysis (ie. only keep frequencies and weights)
    X_train = artists_train.as_matrix()
    X_predict = artists_predict.as_matrix()

    # modeling
    # if artist_archive already has cluster assignments and desired number of playlists is the same and there are new artists to be classified
    if len(Y_train) > 0 and (n_playlists - 1) == max(Y_train) and len(X_predict) > 0:
        # pca = decomposition.PCA(n_components = n_playlists)
        # pca.fit(train_X)
        # train_X = pca.transform(train_X)

        clf = neighbors.KNeighborsClassifier()
        clf.fit(X_train, Y_train)
        clusters = clf.predict(X_predict).tolist()
    else:
        # if artist_archive already has cluster assignments and there are new artists to be classified but the desired number of playlists is different than before
        if len(Y_train) > 0 and (len(X_predict) > 0 or (n_playlists - 1) != max(Y_train)):
            sys.stdout.write("The number of playlists to output has changed since last time. You will lose any manual changes you made to which artists belong in which playlists. Proceed?  [y/n]  ")
            choice = raw_input().lower()

            while True:
                if choice == "y" and len(X_predict) > 0:
                    # pca = decomposition.PCA(n_components = n_playlists)
                    # pca.fit(train_X)
                    # train_X = pca.transform(train_X)

                    clf = neighbors.KNeighborsClassifier()
                    clf.fit(X_train, Y_train)
                    clusters = clf.predict(X_predict).tolist()
                    break
                elif choice == 'y' and len(X_predict) == 0:
                    pca = decomposition.PCA(n_components = n_playlists)
                    pca.fit(X_train)
                    X_train = pca.transform(X_train)

                    clf = cluster.KMeans(init = "random", n_clusters = n_playlists, random_state = 42)
                    clf.fit(X_train)
                    clusters = clf.predict(X_train).tolist()
                    break
                elif choice == "n" and len(X_predict) > 0:
                    pca = decomposition.PCA(n_components = n_playlists)
                    pca.fit(X_predict)
                    X_predict = pca.transform(X_predict)

                    clf = cluster.KMeans(init = "random", n_clusters = n_playlists, random_state = 42)
                    clf.fit(X_predict)
                    clusters = clf.predict(X_predict).tolist()
                    break
                elif choice == "n" and len(X_predict) == 0:
                    clusters = Y_train
                    break
                else:
                    sys.stdout.write("Please respond with 'y' or 'n'.\n")
                    choice = raw_input().lower()
        # if there's nothing new to predict just use the previous cluster assignments
        elif len(X_predict) == 0:
            clusters = Y_train
        else:
            pca = decomposition.PCA(n_components = n_playlists)
            pca.fit(X_predict)
            X_predict = pca.transform(X_predict)

            clf = cluster.KMeans(init = "random", n_clusters = n_playlists, random_state = 42)
            clf.fit(X_predict)
            clusters = clf.predict(X_predict).tolist()

    # add cluster assignment to df for artists with playlist_id of -1
    if len(artists_df.loc[artists_df.playlist_id == -1]) == 0 and len(artists_df) == len(clusters):
        artists_df.playlist_id = clusters
    else:
        artists_df.loc[artists_df.playlist_id == -1, 'playlist_id'] = clusters

    # assign each track to cluster based on artist id
    for track in tracks.iterrows():
        artist_id = track[1]['artist_id']
        track[1]['playlist_id'] = cluster_df.ix[artist_id, "playlist_id"]

    # save tracks data for faster lookup in future
    tracks_out = tracks.to_dict()
    with open("data/track_archive.json", "w") as f:
        json.dump(tracks_out, f)

    # initialize clusters_dict of empty lists
    clusters_dict = {n : None for n in range(0, n_playlists)}
    for n in clusters_dict:
        # put track uris in list in dictionary (dict key is cluster number)
        clusters_dict[n] = zip(tracks[:][tracks.playlist_id == n].index.tolist(), tracks[:][tracks.playlist_id == n].popularity.tolist())
    pdb.set_trace()
    # write out each cluster to text file, as separate playlists
    shutil.rmtree("output")
    os.makedirs("output")
    for n in clusters_dict:
        filename = "playlist_%s.txt" % n
        track_list = clusters_dict[n]
        track_list = sortTuple(track_list, True)
        with open("output/%s" % filename, "w") as f:
            for track in track_list:
                line_out = "spotify:track:%s" % track[0]
                f.write("%s\n" % line_out)
        with open("playlists/%s" % filename, "w") as f:
            artist_list = zip(artists_df.artist[artists_df.playlist_id == n].index, artists_df.artist[artists_df.playlist_id == n].values)
            artist_list = sortTuple(artist_list)
            for artist in artist_list:
                outline = "%s, %s" % (artist[0], unidecode(artist[1]))
                f.write("%s\n" % outline)

    # dataframe (with all columns) to json for saving, cluster column as "playlist_id"
    artists_out = artists_df.T.to_dict()

    with open("data/artist_archive.json", "w") as f:
        json.dump(artists_out, f)

    # dataframe with artist names and playlist ids
    # users can manually edit this csv to help algorithm learn better clusters
    cols = ['artist', 'playlist_id']
    cluster_df = artists_df[cols]
    cluster_df = cluster_df.sort("playlist_id")

    # dataframe (with all columns) to csv for saving, cluster column as "playlist_id"
    with open("data/clusters.csv", "w") as f:
         cluster_df.to_csv(f, index_label = "artist_id", encoding = "utf-8")


if __name__ == "__main__":
    main()
