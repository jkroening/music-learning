######################
## take a spotify playlist and
## given a beginning song (artist name and title)
## direct the user on a choose your adventure
## in building a playlist order based on each
## song's next five most similar tracks using
## spotify audio features metadata
######################

import sys
import pdb
import numpy as np
sys.path.append( "../Modules")
import helpers as hlpr
import spotify_methods as sptfy
import data_methods as dam


def main():

    if len(sys.argv) > 4 and sys.argv[4] == "terms":
        terms = True
    else:
        terms = False

    ## get subset of db based on input.txt
    db, unfound_tracks = hlpr.processInput(terms)

    cols_to_remove = ["spotify_id", "spotify_album_id", "echonest_id", "title",
                      "album", "artist", "echonest_artist_id",
                      "spotify_artist_id", "duration", "time_signature",
                      "loudness"]
    ## "_freqwt" is overkill for the sake of explicitness
    ## as "_freq" is in "_freqwt"
    substr_cols_to_remove = ["_freqwt", "_freq"]

    song = 0
    i = 1
    ids = []
    playlist = []
    artist = ""
    title = ""
    query = ('Enter line number of song to start on: ')
    while song == 0:
        db, unfound_tracks, ids, playlist, artist, title, song = hlpr.chooseTrack(
              db
            , db
            , unfound_tracks
            , ids
            , playlist
            , artist
            , title
            , song
            , i
            , query
        )
        i += 1
        if song > len(db):
            song = 0
        query = 'Select next song (enter number): '

    n = len(db)
    j = True
    k = True
    while not db.empty or not unfound_tracks.empty:
        i += 1
        if k:
            if j: ## first time only
                a = artist
                t = title
            else:
                artist = a
                title = t
                j = False
            neighbors = dam.getSimilarPoints(
                hlpr.dataFrameToMatrix(
                      db
                    , cols_to_remove
                    , substr_cols_to_remove
                    , fillNA = True
                    , centerScale = True
                ).copy()
                , db
                , artist
                , title
                , n
                , stdout = False
            )
            db = db[db.index != song]
        if db.empty and unfound_tracks.empty:
            break
        # print "\nYou just chose: {} - {}".format(artist, title)
        neighbors, unfound_tracks, ids, playlist, artist, title, song = hlpr.chooseTrack(
              db
            , neighbors
            , unfound_tracks
            , ids
            , playlist
            , artist
            , title
            , song
            , i
        )
        if song not in db.index:
            k = False ## skip neighbors because song is from unfound_tracks
        else:
            k = True

        # neighbors.index = np.arange(1, len(neighbors) + 1)
        # print "\n", neighbors[["artist", "title"]], "\n"
        # j = len(neighbors) + 2
        # k = len(neighbors) + len(unfound_tracks) + 1
        # unfound_tracks.index = np.arange(j, k)
        # print "\nSongs without Echonest data:"
        # print "(Similar songs cannot be calculated.)"
        # print unfound_tracks[["artist", "title"]], "\n"
        # selection = int(raw_input('Select next song (enter number): '))
        # if selection in np.arange(j, k):
        #     ids.append(unfound_tracks.spotify_id[selection])
        #     unfound_tracks = unfound_tracks[unfound_tracks.index != selection]
        # while selection not in range(1, len(db) + 1):
        #     selection = int(raw_input('Select next song (enter number): ')
        # if selection in np.arange(1:len(neighbors)):
        #     next_song = neighbors[neighbors.index == selection]
        #     spotify_id = next_song.spotify_id.values[0]
        #     echonest_id = next_song.echonest_id.values[0]
        #     title = next_song.title.values[0]
        #     artist = db.artist[song]
        #     title = db.title[song]
        #     ids.append(spotify_id)
        #     playlist.append("{}. {} - {}".format(i, artist, title))
        # song = np.bincount(np.concatenate(
        #     (db.index[db.echonest_id == echonest_id].values,
        #      db.index[db.spotify_id == spotify_id].values,
        #      db.index[db.title == title].values)
        # )).argmax()

    sptfy.writeIDsToURI(ids, "../output", "adventure.txt")
    print "\n\nHere is your track order:\n"
    for p in playlist:
        print p


if __name__ == "__main__":
    main()
