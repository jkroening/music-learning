import sys
import json
import fileinput
import urllib2
import pdb
sys.path.append( "../Modules")
from helpers import loadFile
import spotify_methods as sp

def spotifyLookup(track_id):
    track_string = 'http://ws.spotify.com/lookup/1/.json?uri=spotify:track:%s' % track_id.strip()
    try:
        response = urllib2.urlopen(track_string)
        data = json.loads(response.read())
        track_data = [data['track']['href'], data['track']['artists'][0]['name'], data['track']['name'], data['track']['popularity'][0:4]]
        return track_data
    except:
        print("Trouble finding track_id:  %s" % track_id.strip())
        return spotifyLookup(track_id)

def main():

    cleans = []
    explicits = []
    local_tracks = []
    for line in fileinput.input('cleans.txt'):
        if 'local' in line:
            local_tracks.append(line)
            continue
        track_id = line.strip('http://open.spotify.com/track/')
        track_data = sp.pullSpotifyTrack(track_id)
        cleans.append(track_data)
    for line in fileinput.input('explicits.txt'):
        if 'local' in line:
            local_tracks.append(line)
            continue
        track_id = line.strip('http://open.spotify.com/track/')
        track_data = sp.pullSpotifyTrack(track_id)
        explicits.append(track_data)
        # track_list.append([str('spotify:track:%s' % track_id).strip(), track_id.strip(), '0.00'])

    # sort explicit list
    sorted_tracks = sorted(explicits, key=lambda x: float(x['popularity']), reverse=True)
    # print sorted_tracks
    # for item in sorted_tracks:
    #     print item[1] + " - " + item[2], item[3]
    # for item in sorted_tracks:
    #     print item[0]

    # now replace explicits with cleans
    for e in explicits: # replace explicit track href by the clean version's href
        for c in cleans:
            if e['artist'] in c['artist'] and e['title'][:3] in c['title'][:3]: # compare artist name and first 4 characters of track name
                e['spotify_id'] = c['spotify_id']
    # sorted_tracks = sorted(explicits, key=lambda x: float(x[3]), reverse=True)
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
