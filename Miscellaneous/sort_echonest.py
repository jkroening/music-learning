######################
## given an input of spotify songs
## sort the songs by a given echonest metadata feature
## and output the sorted spotify uris
######################

import sys
import os
import shutil
import pdb
sys.path.append( "../Modules")
from helpers import loadFile, writeTextFile
import spotify_methods as sp
from db_methods import lookupSongBySpotifyID, lookupSongByEchoNestID, saveDataFrame, subsetDataFrame
from echonest_methods import pullEchoNestSong, searchEchoNestSong


def main():

    ## set echonest API key
    config = loadFile("../config", "config.csv", True)
    api_key = config['ECHONEST_API_KEY']

    # ## load tracks in playlist
    in_tracks = loadFile("input", "input.txt")
    
    ## load database of metadata
    echonest_song_db = loadFile("../Databases", "echonest_song_db.csv")
    shutil.copyfile("../Databases/echonest_song_db.csv", "../Databases/_Backup/echonest_song_db.csv")
    echonest_artist_db = loadFile("../Databases", "echonest_artist_db.csv")
    shutil.copyfile("../Databases/echonest_artist_db.csv", "../Databases/_Backup/echonest_artist_db.csv")

    local_tracks = []
    for track in in_tracks:
        if 'local' in track:
            local_tracks.append(track)
            song = searchEchoNestSong(api_key, track)
            if not lookupSongByEchoNestID(song['echonest_id'], echonest_song_db):
                if song is not None:
                    echonest_song_db = echonest_song_db.append(song, ignore_index = True)
                else:
                    print "{} not found.".format(track)
        else:
            if not lookupSongBySpotifyID(track, echonest_song_db):
                song = pullEchoNestSong(api_key, track)
                if song is not None:
                    echonest_song_db = echonest_song_db.append(song, ignore_index = True)
                else:
                    print "{} not found.".format(track.strip())
    saveDataFrame(echonest_song_db, "../Databases", "echonest_song_db.csv")

    ## subset song database on tracks in playlist
    db_subset = subsetDataFrame(echonest_song_db, in_tracks)

    ## which feature to sort on
    sort_col = sys.argv[1]
    ## ascending or descending (1 = ascending, 0 = descending)
    ascending = int(sys.argv[2])

    sorted_db = db_subset.sort(sort_col, ascending = ascending)
    sorted_tracks = ["spotify:track:{}".format(x[1]['spotify_id']) if len(x[1]['spotify_id']) < 36 else x[1]['spotify_id'] for x in sorted_db.iterrows()]

    writeTextFile(sorted_tracks, "output", "walk.txt")

    # print sorted_tracks
    for item in sorted_tracks:
        print item


if __name__ == "__main__":
    main()