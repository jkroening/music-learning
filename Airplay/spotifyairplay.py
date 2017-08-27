import sys
import json
import fileinput
import urllib2
import re
import pdb
sys.path.append( "../Modules")
import spotify_methods as sptfy
from helpers import loadFile


def main(ultimatechart, explicit = False):

    cleans = []
    explicits = []
    local_tracks = []

    config = loadFile("../config", "config.csv", True)
    token = sptfy.authSpotipy()

    cleans, local_tracks = sptfy.pullSpotifyTracks('../input', 'cleans.txt', token = token)
    explicits, local_tracks = sptfy.pullSpotifyTracks(
          '../input', 'explicits.txt'
        , tracks = explicits
        , local_tracks = local_tracks
        , token = token
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

    print "\n"
    for item in sorted_tracks:
        print str(item['popularity']) + " :: " + item['artist'] + " - " + item['title']
    print "\n"
    for item in sorted_tracks:
        print "spotify:track:{}".format(item['spotify_id'].strip())
    for item in local_tracks:
        print item
    print "\n"

    if ultimatechart is not None:
        nums = ('01', '02', '03', '04', '05', '06', '07', '08', '09') + tuple(str(x) for x in range(10, 101))
        uc = [item for item in ultimatechart if item.startswith(nums)]
        print "Look into keeping the following songs in Airplay this week...\n"
        for item in sorted_tracks:
            if item['popularity'] < 75:
                artist = item['artist']
                title = item['title']
                artist = re.sub("&", "and", re.sub(r'([^\s\w]|_)+', '', artist).lower())
                title = re.sub("&", "and", re.sub(r'([^\s\w]|_)+', '', title).lower())
                for u in uc:
                    x = re.sub(r'([^\s\w]|_)+', '', re.sub("&", "and", u)).lower()
                    if artist + " " in x:
                        artist_match = True
                    else:
                        artist_match = False
                    if title + " by" in x:
                        title_match = True
                    else:
                        title_match = False
                    xs = [i for i in x.split(" ")]
                    if title_match or (artist_match and any([True for t in title.split(" ") if t in xs])):
                        print str(item['popularity']) + " :: " + item['artist'] + " - " + item['title']
                        break
    else:
        print "If you want to compare to Ultimate Chart, please provide a txt version as an arg."


if __name__ == "__main__":
    explicit = False
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r') as f:
            ultimatechart = f.readlines()
        if len(sys.argv) == 3 and sys.argv[2] == 'explicit':
            explicit = True
    else:
        ultimatechart = None
        print "If you want to compare to Ultimate Chart, please provide a txt version as an arg."

    main(ultimatechart, explicit)
