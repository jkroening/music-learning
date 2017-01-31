######################
## take an itunes exported playlist
## find all the songs in spotify and
## output a list of matching spotify ids
######################

import sys
import csv
import pdb
sys.path.append( "../Modules")
import helpers as hlpr
import spotify_methods as sptfy


def main():

    playlist_file = sys.argv[1]

    outlist = []
    with open(playlist_file, "U") as f:
        for line in csv.reader(f, dialect = "excel-tab"):
            if "Date Modified" in line:
                continue
            name = line[0].strip()
            artist = line[1].strip()
            album = line[3].replace("|EFA|", "").replace("[EFA]", "").replace(
                "[EP]", "").replace("[Deluxe]", "").replace(
                    "[Deluxe Edition]", "").replace("[Single]", "").replace(
                        " - Single", "").replace(" - EP", "").replace(
                            "(Deluxe Edition)", "").replace("[", "").replace(
                                "]", "").strip()
            if "B-Sides" in album:
                album = ""
            print "%s - %s - %s" % (name, artist, album)
            track_id = sptfy.searchSpotifyTrack(artist, name, album)
            if len(track_id) == 0:
                track_id = sptfy.searchSpotifyTrack(artist, name)
            print(track_id)
            outlist.append(track_id)

    with open("../output/spotify_tracks.txt", "w") as f:
        for item in [item for o in outlist for item in o]:
            f.write("%s\n" % item)


if __name__ == "__main__":
    main()
