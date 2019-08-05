######################
## take a spotify playlist and
## given a beginning song (artist name and title)
## output a playlist order based on
## audio_features metadata similarity between songs
######################

import sys
import os
import pdb
from subprocess import call
import scipy.spatial.distance as sc
import numpy as np
sys.path.append( "../Modules")
import spotify_methods as sptfy
import helpers as hlpr
import data_methods as dam
import dijkstra
import tsp_solver.greedy as tspg


def main():

    if len(sys.argv) > 1 and sys.argv[1] == "genres":
        genres = True
    else:
        genres = False

    ## get subset of db based on input.txt
    db, unfound_tracks = hlpr.processInput(genres = genres)

    cols = ['tempo', 'mode', 'acousticness', 'danceability', 'energy',
            'instrumentalness', 'liveness', 'speechiness', 'valence']
    if genres:
        cols = cols + GENRE_AGGREGATES

    X = hlpr.dataFrameToMatrix(
        db,
        cols_to_keep = cols,
        fillNA = True,
        centerScale = True
    )
    # X = X.fillna(0)
    # X = dam.minMaxScaleData(X)
    # X2 = dam.transformPCA(X, 2)
    # clusters2 = dam.classifyUnsupervised(X2, 3)
    # clusters1 = dam.classifyUnsupervised(X, 3)

    method = raw_input(
        "Which method: Start and end? Enter 'both'.\nJust start song? Enter 'start'. >> "
    )

    if method == "both":
        D = sc.pdist(X.copy())
        D = sc.squareform(D)

        db_dict = db.to_dict('index')

        D_dict = dict(zip(db_dict, D))

        G = {}
        for k1 in db_dict:
            G[k1] = dict(zip(db_dict, D_dict[k1]))

        tspg.solve_tsp(D)

        def find_all_paths(graph, start, end, path=[]):
            path = path + [start]
            if start == end:
                return [path]
            if not graph.has_key(start):
                return []
            paths = []
            for node in graph[start]:
                if node not in path:
                    newpaths = find_all_paths(graph, node, end, path)
                    for newpath in newpaths:
                        paths.append(newpath)
            return paths

        start_artist = raw_input('Enter artist name of song to start with: ')
        start_title = raw_input('Enter title of song to start with: ')
        end_artist = raw_input('Enter artist name of song to end with: ')
        end_title = raw_input('Enter title of song to end with: ')

        df = db
        start = np.where((df.artist.str.lower() == start_artist.lower()) &
                         (df.title.str.lower() == start_title.lower()))[0][0]
        end = np.where((df.artist.str.lower() == end_artist.lower()) &
                       (df.title.str.lower() == end_title.lower()))[0][0]

        row = np.repeat(999, len(D))
        col = np.append(row, 0)
        col.shape = (len(col), 1)
        col[start] = 0
        col[end] = 0
        row[start] = 0
        row[end] = 0

        DD = np.append(D, [row], 0)
        DD = np.append(DD, col, 1)

        tsp = tspg.solve_tsp(DD)

        with open(os.path.join("../output", "walk.txt"), "w") as f:
            mid = np.where(np.array(tsp) == (len(DD) - 1))[0][0]
            if db.iloc[tsp[mid + 1], ].title.lower() == start_title:
                walk = np.concatenate([tsp[(mid + 1):len(tsp)], tsp[0:mid]])
            elif db.iloc[tsp[mid - 1], ].title.lower() == start_title:
                walk = np.concatenate([tsp[0:(mid)][::-1], tsp[(mid + 1):len(tsp)][::-1]])
            for w in walk:
                if w == tsp[0]:
                    print "----------------------------------------"
                print "{} - {}".format(db.iloc[w, ].artist,
                                           db.iloc[w, ].title)
            print("\n")
            for w in walk:
                print "spotify:track:{}".format(db.iloc[w, ].spotify_id)
                f.write("spotify:track:%s\n" % w)

    if method == "start":
        strategy = raw_input("Join songs by 'link' or by 'center'? ")
        artist = raw_input('Enter artist name: ')
        song = raw_input('Enter song name: ')

        ## center means songs are sorted/ordered by proximity to centroid song
        if strategy == "center":
            expanse = dam.expandToPoints(X.copy(), db, artist, song)
            ids = expanse.spotify_id.tolist()
            sptfy.writeIDsToURI(ids, "../output", "walk.txt")
            for i in ids:
                print "{} - {}".format(
                    db.artist.values[db.spotify_id.values == i][0],
                    db.title.values[db.spotify_id.values == i][0]
                )
            print("\n")
            for i in ids:
                print "spotify:track:{}".format(i)

        ## link means songs are strung together finding the next closest song to
        ## the previously added node
        elif strategy == "link":
            walk = dam.walkPoints(X.copy(), db, artist, song)
            hlpr.writeTextFile(walk, "../output", "walk.txt")
            for w in walk:
                print "{} - {}".format(
                    db.artist.values[
                        db.spotify_id.values == sptfy.stripSpotifyURI(w)
                    ][0],
                    db.title.values[
                        db.spotify_id.values == sptfy.stripSpotifyURI(w)
                    ][0]
                )
            print("\n")
            for w in walk:
                print w

        # cluster_groups1 = hlpr.separateMatrixClusters(X2, clusters1)
        # cluster_groups2 = hlpr.separateDataFrameClusters(db_subset, clusters2)
        # cluster_groups3 = hlpr.separateDataFrameClusters(db_subset, clusters1)
        # scatterplot(X, "fit_predict")

        ## open file in sublime text
        # call(["subl", "output/walk.txt"])

    if len(unfound_tracks) > 0:
        print "\nThese songs weren't found..."
        print "Please add them back to your playlist manually:"
        for item in unfound_tracks:
            print item.strip()
        print "\n"


if __name__ == "__main__":
    main()
