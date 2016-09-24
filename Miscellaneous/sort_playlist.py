######################
## given an input of spotify songs
## sort the songs by a given audio
## feature metadata and output the
## sorted spotify URIs
######################

import sys
import os
import pdb
sys.path.append("../Modules")
import pandas as pd
import helpers as hlpr
import db_methods as dbm
import spotify_methods as sptfy

def main():

    ## which feature to sort on
    sort_col = raw_input(
        "\nEnter one of the following features to sort on:\ntitle\nartist\nalbum\nduration\ntempo\ntime_signature\nkey\nmode\nloudness\nacousticness\ndanceability\nenergy\ninstrumentalness\nliveness\nspeechiness\nvalence\npopularity\n\n"
    )

    ## ascending or descending (1 = ascending, 0 = descending)
    ascending = int(raw_input("\nChoose order:\n(0) descending\n(1) ascending\n\n"))
    while ascending != 0 and ascending != 1:
        ascending = int(raw_input("\nEnter either 0 or 1:\n(0) descending\n(1) ascending\n\n"))

    if sort_col == "popularity":
        db, unfound_tracks = sptfy.pullSpotifyTracks('../input/input.txt')
        db = pd.DataFrame.from_dict(db)
    else:
        ## get subset of db based on input.txt
        db, unfound_tracks = hlpr.processInput()

    if sort_col not in db.columns:
        print("\nSort column '{}' not in database!").format(sort_col)
        sys.exit()

    sorted_db = db.sort_values(by = sort_col, ascending = ascending)
    sorted_tracks = [
        "spotify:track:{}".format(x[1]['spotify_id']).rstrip() \
        if len(x[1]['spotify_id']) < 36 else x[1]['spotify_id'].rstrip() \
        for x in sorted_db.iterrows()
    ]

    hlpr.writeTextFile(sorted_tracks, "../output", "sorted_playlist.txt")
    print("\n")
    print("\n".join(sorted_tracks))

if __name__ == "__main__":
    main()
