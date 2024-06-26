import sys
import json
import fileinput
import re
import argparse
import pdb
sys.path.append( "../Modules")
import spotify_methods as sptfy
from helpers import loadFile


def main(ags, explicit = False):

    if args.billboardchart is not None:
        with open(args.billboardchart, 'r') as f:
            billboardchart = [line.rstrip() for line in f]
    else:
        billboardchart = None

    cleans = []
    explicits = []
    local_tracks = []

    config = loadFile("../config", "config.csv", True)
    try:
        token = sptfy.authSpotipy()
    except:
        token = None
    sptpy = sptfy.getSpotifyCred()

    cleans, local_tracks = sptfy.pullSpotifyTracks(
        '../input', 'cleans.txt', sptpy = sptpy
    )
    explicits, local_tracks = sptfy.pullSpotifyTracks(
          '../input', 'explicits.txt',
        tracks = explicits,
        local_tracks = local_tracks,
        sptpy = sptpy
    )

    if explicit:
        # sort explicit list
        sorted_tracks = sorted(explicits, key=lambda x: float(x['popularity']), reverse=True)
    else:
        # sort explicit list
        sorted_tracks = sorted(explicits, key=lambda x: float(x['popularity']), reverse=True)
        # now replace explicits with cleans
        for e in explicits: # replace explicit track href by the clean version's href
            for c in cleans:
                if e['artist'] in c['artist'] and e['title'][:3] in c['title'][:3]: # compare artist name and first 4 characters of track name
                    e['spotify_id'] = c['spotify_id']

    print("\n")
    for item in sorted_tracks:
        print(str(item['popularity']) + " :: " + item['artist'] + " - " + item['title'])
    print("\n")
    for item in sorted_tracks:
        print("spotify:track:{}".format(item['spotify_id'].strip()))
    for item in local_tracks:
        print(item)
        print("\n")

    if billboardchart is not None:
        print("\nLook into keeping the following songs in Airplay this week...\n")
        for item in sorted_tracks:
            if item['popularity'] < 75:
                artist = item['artist']
                title = item['title']
                artist = re.sub("&", "and", re.sub(r'([^\s\w]|_)+', '', artist).lower())
                title = re.sub("&", "and", re.sub(r'([^\s\w]|_)+', '', title).lower())
                for u in billboardchart:
                    x = re.sub(r'([^\s\w]|_)+', '', re.sub("&", "and", u)).lower()
                    if artist in x:
                        artist_match = True
                    else:
                        artist_match = False
                    if title in x:
                        title_match = True
                    else:
                        title_match = False
                    xs = [i for i in x.split(" ")]
                    if title_match or (artist_match and any([True for t in title.split(" ") if t in xs])):
                        print(str(item['popularity']) + " :: " + item['artist'] + " - " + item['title'])
                        break
    else:
        print("\nIf you want to compare to Billboard Chart, please provide a txt version as an arg to --billboardchart\n")

    print("\n")

if __name__ == "__main__":
    explicit = False
    parser = argparse.ArgumentParser()
    parser.add_argument('--billboardchart')
    parser.add_argument('--explicit')
    args = parser.parse_args()

    if args.explicit:
        explicit = args.explicit

    main(args, explicit)
