######################
## take a spotify playlist and
## given a beginning song (artist name and title)
## output a playlist order based on
## audio_features metadata similarity between songs
######################

import sys
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

    terms = True
    # if len(sys.argv) > 4 and sys.argv[4] == "terms":
    #     terms = True
    # else:
    #     terms = False

    ## get subset of db based on input.txt
    db, unfound_tracks = hlpr.processInput(terms)

    cols_to_remove = ["spotify_id", "spotify_album_id", "echonest_id", "title",
                      "album", "artist", "echonest_artist_id",
                      "spotify_artist_id", "duration", "time_signature",
                      "loudness"]
    ## "_freqwt" is overkill for the sake of explicitness
    ## as "_freq" is in "_freqwt"
    substr_cols_to_remove = ["_freqwt", "_freq"]

    X = hlpr.dataFrameToMatrix(db, cols_to_remove, substr_cols_to_remove)
    # X = X.fillna(0)
    X = dam.minMaxScaleData(X)
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

        df = db_subset
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

        for i in tsp:
            if i != len(DD) - 1:
                print "{} - {}".format(db.iloc[i, ].artist,
                                       db.iloc[i, ].title)
            else:
                print "--------------------------------"

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
