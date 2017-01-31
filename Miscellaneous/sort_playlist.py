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
    sort_col1 = raw_input(
        "\nEnter one of the following features to sort on:\ntitle\nartist\nalbum\nduration\ntempo\ntime_signature\nkey\nmode\nloudness\nacousticness\ndanceability\nenergy\ninstrumentalness\nliveness\nspeechiness\nvalence\npopularity\nrelease_date\nyear\n\n"
    )
    ## ascending or descending (1 = ascending, 0 = descending)
    ascending1 = int(raw_input("\nChoose sort order for this feature:\n(0) descending\n(1) ascending\n\n"))
    while ascending1 != 0 and ascending1 != 1:
        ascending1 = int(raw_input("\nEnter either 0 or 1:\n(0) descending\n(1) ascending\n\n"))

    if sort_col1 in ["tempo", "time_signature", "key", "mode", "popularity", "release_date", "year"]:
        sort_col2 = raw_input(
            "\nIn case of ties what second feature would you like to sort on:\ntitle\nartist\nalbum\nduration\ntempo\ntime_signature\nkey\nmode\nloudness\nacousticness\ndanceability\nenergy\ninstrumentalness\nliveness\nspeechiness\nvalence\npopularity\nrelease_date\nyear\n\n"
        )
        ## ascending or descending (1 = ascending, 0 = descending)
        ascending2 = int(raw_input("\nChoose sort order for this feature:\n(0) descending\n(1) ascending\n\n"))
        while ascending2 != 0 and ascending2 != 1:
            ascending2 = int(raw_input("\nEnter either 0 or 1:\n(0) descending\n(1) ascending\n\n"))
    else:
        sort_col2 = None
        ascending2 = 1
    print("")

    if "popularity" in [sort_col1, sort_col2]:
        db, unfound_tracks = sptfy.pullSpotifyTracks('../input/input.txt')
        df = pd.DataFrame.from_dict(db)
        db, unfound_tracks = hlpr.processInput(input_playlist = "input.txt")
        db = db.merge(df[["spotify_id", "popularity"]], on = "spotify_id")
    else:
        ## get subset of db based on input.txt
        db, unfound_tracks = hlpr.processInput(input_playlist = "input.txt")

    if sort_col1 not in db.columns:
        print("\nSort column '{}' not in database!").format(sort_col1)
        sys.exit()
    if sort_col2 is not None and sort_col2 not in db.columns:
        print("\nSort column '{}' not in database!").format(sort_col2)
        sys.exit()

    if sort_col2 is None:
        sorted_db = db.sort_values(by = sort_col1, ascending = ascending1)
    else:
        sorted_db = db.sort_values(by = [sort_col1, sort_col2], ascending = [ascending1, ascending2])
    sorted_tracks = [
        "spotify:track:{}".format(x[1]['spotify_id']).rstrip() \
        if len(x[1]['spotify_id']) < 36 else x[1]['spotify_id'].rstrip() \
        for x in sorted_db.iterrows()
    ]

    print("\n")
    print(sorted_db[["artist", "title"]])

    hlpr.writeTextFile(sorted_tracks, "../output", "sorted_playlist.txt")
    print("\n")
    print("\n".join(sorted_tracks))

    if len(unfound_tracks) > 0:
        print("\nAdd these local tracks wherever you want in the playlist:\n")
        print("\n".join(unfound_tracks))

if __name__ == "__main__":
    main()
