######################
## sort a spotify playlist by popularity
######################

import sys
import json
import fileinput
import pdb
import urllib2
sys.path.append( "../Modules")
from helpers import loadFile
import spotify_methods as sp

def spotifyLookup(track_id):
    track_string = 'http://ws.spotify.com/lookup/1/.json?uri=spotify:track:%s' % track_id.strip()
    try:
        response = urllib2.urlopen(track_string)
        data = json.loads(response.read())
        track_data = [data['track']['href'], data['track']['name'], data['track']['popularity'][0:4]]
        return track_data
    except:
        return spotifyLookup(track_id)

def main():
    if len(sys.argv) > 1:
        in_tracks = loadFile("", sys.argv[1])
    else:
        in_tracks = loadFile("input", "input.txt")
    track_list = []
    local_tracks = []
    for line in in_tracks:
        if "local" in line:
            local_tracks.append(line)
            continue
        track_id = line.strip('http://open.spotify.com/track/')
        track_data = sp.pullSpotifyTrack(track_id)
        track_list.append(track_data)
        # track_list.append([str('spotify:track:%s' % track_id).strip(), track_id.strip(), '0.00'])
    pdb.set_trace()
    sorted_tracks = sorted(track_list, key=lambda x: float(x['popularity']), reverse=True)
    # print sorted_tracks
    print "\n"
    for item in sorted_tracks:
        print str(item['popularity']) + " :: " + item['artist'] + " - " + item['title']
    print "\n"
    for item in sorted_tracks:
        print "spotify:track:{}".format(item['spotify_id'].strip())
    for item in local_tracks:
        print item
    print "\n"

if __name__ == "__main__":
    main()
