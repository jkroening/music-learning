import sys
import json
import fileinput
import urllib2

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

    if len(sys.argv) < 2:
        cleans = []
        explicits = []
        for line in fileinput.input('cleans.txt'):
            track_id = line.strip('http://open.spotify.com/track/')
            track_data = spotifyLookup(track_id)
            cleans.append(track_data)
        for line in fileinput.input('explicits.txt'):
            track_id = line.strip('http://open.spotify.com/track/')
            track_data = spotifyLookup(track_id)
            explicits.append(track_data)
            # track_list.append([str('spotify:track:%s' % track_id).strip(), track_id.strip(), '0.00'])

        # sort explicit list
        sorted_tracks = sorted(explicits, key=lambda x: float(x[3]), reverse=True)
        # print sorted_tracks
        # for item in sorted_tracks:
        #     print item[1] + " - " + item[2], item[3]
        # for item in sorted_tracks:
        #     print item[0]

        # now replace explicits with cleans
        for e in explicits: # replace explicit track href by the clean version's href
            for c in cleans:
                if e[1] in c[1] and e[2][:3] in c[2][:3]: # compare artist name and first 4 characters of track name
                    e[0] = c[0]
        # sorted_tracks = sorted(explicits, key=lambda x: float(x[3]), reverse=True)
        # print sorted_tracks
        for item in sorted_tracks:
            print item[1] + " - " + item[2], item[3]
        for item in sorted_tracks:
            print item[0]
    else:
        tracks = []
        with open(sys.argv[1]) as infile:
            for f in infile.readlines():
                track_id = f.strip('http://open.spotify.com/track/')
                track_data = spotifyLookup(track_id)
                tracks.append(track_data)
        # sort list
        sorted_tracks = sorted(tracks, key=lambda x: float(x[3]), reverse=True)
        # print sorted_tracks
        for item in sorted_tracks:
            print item[1] + " - " + item[2], item[3]
        for item in sorted_tracks:
            print item[0]


if __name__ == "__main__":
    main()
