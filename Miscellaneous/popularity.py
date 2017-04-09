######################
## sort a spotify playlist by popularity
######################

import sys
import pdb
import fileinput
sys.path.append( "../Modules")
import spotify_methods as sptfy
from helpers import loadFile


def main():
    if len(sys.argv) > 1:
        in_file = sys.argv[1]
    else:
        in_file = "../input/input.txt"
    track_list = []
    local_tracks = []

    config = loadFile("../config", "config.csv", True)
    token = sptfy.authSpotipy()

    for line in fileinput.input(in_file):
        if "local" in line:
            local_tracks.append(line)
            continue
        track_id = sptfy.stripSpotifyLink(line)
        track_data = sptfy.pullSpotifyTrack(track_id, token = token)
        track_list.append(track_data)
    sorted_tracks = sorted(
        track_list,
        key = lambda x: float(x['popularity']),
        reverse = True
    )
    print "\n"
    for item in sorted_tracks:
        print str(item['popularity']) + " :: " + item['artist'] + \
            " - " + item['title']
    print "\n"
    for item in sorted_tracks:
        print "spotify:track:{}".format(item['spotify_id'].strip())
    for item in local_tracks:
        print item
    print "\n"


if __name__ == "__main__":
    main()
    if (grepl("new_eps.csv"))
