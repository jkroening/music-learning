######################
## sort spotify playlists by spotify genres
## using lists of spotify subgenres
## separated as config files
######################

import spotipy
import fileinput
import sys
import os
import pdb
sys.path.append( "../Modules")
import spotify_methods as sptfy
import db_methods as dbm
import helpers and hlpr


def main():
    genres = dbm.buildSubgenres()

    if len(sys.argv) > 1:
        in_file = sys.argv[1]
    else:
        in_file = "../input/input.txt"

    token = sptfy.authSpotipy()

    os.remove("../output/*.txt")

    for line in fileinput.input(in_file):
        track_id = line.strip('http://open.spotify.com/track/').strip()
        artist_id = sptfy.pullSpotifyTrack(track_id)['spotify_artist_id']
        hlpr.sortGenres(artist_id, genres, track_id, token, makePlaylists = True)

if __name__ == "__main__":
    main()
