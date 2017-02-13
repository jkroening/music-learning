######################
## sort spotify playlists by spotify genres
## using lists of spotify subgenres
## separated as config files
######################

import spotipy
import fileinput
import sys
import os
import glob
sys.path.append( "../Modules")
import spotify_methods as sptfy
import db_methods as dbm
import helpers as hlpr
import module_helpers as mhlpr


def main():

    if len(sys.argv) > 1:
        in_file = sys.argv[1]
    else:
        in_file = "../input/input.txt"

    token = sptfy.authSpotipy()

    for f in glob.glob("../output/*.txt"):
        os.remove(f)

    for line in fileinput.input(in_file):
        track_id = line.split("/")[-1].strip()
        track_info = sptfy.pullSpotifyTrack(track_id)
        artist_id = track_info['spotify_artist_id']
        artist_name = track_info['artist']
        track_name = track_info['title']
        secondary_artist = track_info['secondary_artist']
        hlpr.sortGenres(artist_name, artist_id, track_name, track_id,
                        secondary_artist, token, makePlaylists = True)

if __name__ == "__main__":
    main()
