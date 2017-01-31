######################
## given a song (artist name and title, album title is optional)
## find any of the user's playlists that
## contain the song
######################

import sys
import pdb
sys.path.append( "../Modules")
import helpers as hlpr
import spotify_methods as sptfy


def main():

    username = sys.argv[1]
    artist = sys.argv[2]
    title = sys.argv[3]
    if len(sys.argv) > 4:
        album = sys.argv[4]
    else:
        album = None

    config = hlpr.loadFile("../config", "config.csv", True)

    app = sptfy.authSpotify(config)
    app.run()

    sp = sptfy.getSpotifyCred(username, config)

    tracks = sptfy.searchSpotifyTrack(artist, title, album)

    sptfy.searchUserPlaylists(sp, username, tracks)
    print "\n"


if __name__ == "__main__":
    main()
