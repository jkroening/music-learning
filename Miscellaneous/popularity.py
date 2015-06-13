######################
## sort a spotify playlist by popularity
######################

import sys
import json
import fileinput
import urllib2

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
    track_list = []
    for line in fileinput.input(sys.argv[1]):
        track_id = line.strip('http://open.spotify.com/track/')
        track_data = spotifyLookup(track_id)
        track_list.append(track_data)
        # track_list.append([str('spotify:track:%s' % track_id).strip(), track_id.strip(), '0.00'])
    sorted_tracks = sorted(track_list, key=lambda x: float(x[2]), reverse=True)
    # print sorted_tracks
    for item in sorted_tracks:
        print item[1], item[2]
    for item in sorted_tracks:
        print item[0]

if __name__ == "__main__":
    main()
