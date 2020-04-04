######################
## take a playlist and shorten it to the specified length
## with a preference for songs that are high on two parameters, chosen from:
## popularity, recency (year), valence, energy, acousticness, danceability
######################

import sys
import pdb
sys.path.append( "../Modules")
import helpers as hlpr
import pandas as pd
import numpy as np
import spotify_methods as sptfy


def main():

    track_list = hlpr.loadFile("../input", "input.txt")
    desired_len = int(input(
        "\nHow many tracks would you like the playlist to be? "
    ))
    num_to_drop = len(track_list) - desired_len
    sort_col1 = input(
        "\nEnter one of the following features to sort on: \
        \nacousticness\ndanceability\nenergy\nvalence\npopularity \
        \nrelease_date\nyear\n\n"
    )
    ascending1 = int(input(
        "\nChoose sort order for this feature: \
        \n(0) descending\n(1) ascending\n\n"
    ))
    sort_col2 = input(
        "\nEnter another feature to sort on (blank to sort on one feature only): \
        \nacousticness\ndanceability\nenergy\nvalence\npopularity \
        \nrelease_date\nyear\n\n"
    )
    if sort_col2 != '':
        ascending2 = int(input(
            "\nChoose sort order for this feature: \
            \n(0) descending\n(1) ascending\n\n"
        ))
    else:
        sort_col2 = None
        ascending2 = 1

    config = hlpr.loadFile("../config", "config.csv", True)
    token = sptfy.authSpotipy()

    if "popularity" in [sort_col1, sort_col2]:
        db, unfound_tracks = sptfy.pullSpotifyTracks('../input',
                                                     'input.txt',
                                                     token = token)
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

    sorted_db1 = db.sort_values(by = sort_col1, ascending = ascending1)
    if sort_col2 is not None:
        sorted_db2 = db.sort_values(by = sort_col2, ascending = ascending2)

    lst1 = sorted_db1.index.values
    lst2 = sorted_db2.index.values

    i = len(track_list) - num_to_drop
    remove = np.intersect1d(lst1[i:], lst2[i:])

    while len(remove) < num_to_drop:
        i -= 1
        remove = np.intersect1d(lst1[i:], lst2[i:])

    keep = [i for i in db.index if i not in remove]

    remove_db = db.loc[remove, ]
    keep_tracks = [
        "spotify:track:{}".format(x[1]['spotify_id']).rstrip() \
        if len(x[1]['spotify_id']) < 36 else x[1]['spotify_id'].rstrip() \
        for x in db.loc[keep, ].iterrows()
    ]
    remove_db = remove_db.sort_values(by = [sort_col1, sort_col2],
                                      ascending = [ascending1, ascending2])
    remove_tracks = [
        "spotify:track:{}".format(x[1]['spotify_id']).rstrip() \
        if len(x[1]['spotify_id']) < 36 else x[1]['spotify_id'].rstrip() \
        for x in remove_db.iterrows()
    ]

    print("\nThese songs will be removed:\n")
    pd.set_option('display.max_rows', None)
    print(remove_db[['artist', 'title', sort_col1, sort_col2]])
    print("")
    print("\n".join(remove_tracks))

    print("\n\nThese songs remain:\n")
    print("\n".join(keep_tracks))

    if len(unfound_tracks) > 0:
        print("\nAdd these local tracks wherever you want in the playlist:\n")
        print("\n".join(unfound_tracks))

    # hlpr.writeTextFile(track_list, "../output", "output.txt")


if __name__ == "__main__":
    main()
