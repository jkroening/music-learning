######################
## sort spotify playlists by spotify genres
## using lists of spotify subgenres
## separated as config files
######################

import spotipy
import fileinput
import sys

def buildSubgenres():
    pop, urban, rock = [], [], []
    for line in fileinput.input('config/pop.txt'):
        pop.append(line.strip())
    for line in fileinput.input('config/urban.txt'):
        urban.append(line.strip())
    for line in fileinput.input('config/rock.txt'):
        rock.append(line.strip())
    return pop, urban, rock

def getArtist(track_id):
    sp = spotipy.Spotify()
    track = sp.track(track_id)
    artist_id = track['artists'][0]['uri']
    artist = track['artists'][0]['name']
    return artist_id, artist

def getGenres(artist_id):
    sp = spotipy.Spotify()
    artist = sp.artist(artist_id)
    return artist['genres']

def sortGenres(artist_id, pop, urban, rock, track_id):
    p, u, r = 0, 0, 0
    sp = spotipy.Spotify()
    artist = sp.artist(artist_id)
    if len(artist['genres']) < 1:
        with open('output/unknowntracks.txt', 'a') as f:
            f.write('spotify:track:%s\r' % track_id)
            print artist
    else:
        for g in artist['genres']:
            if g in pop:
                p = p + 1
            if g in urban:
                u = u + 1
            if g in rock:
                r = r + 1
        # if there are ties, take the first genre listed of the ties
        if p == u and p > r:
            if artist['genres'][0] in pop:
                with open('output/poptracks.txt', 'a') as f:
                    f.write('spotify:track:%s\r' % track_id)
            elif artist['genres'][0] in urban:
                with open('output/urbantracks.txt', 'a') as f:
                    f.write('spotify:track:%s\r' % track_id)
        elif p == r and p > u:
            if artist['genres'][0] in pop:
                with open('output/poptracks.txt', 'a') as f:
                    f.write('spotify:track:%s\r' % track_id)
            elif artist['genres'][0] in rock:
                with open('output/rocktracks.txt', 'a') as f:
                    f.write('spotify:track:%s\r' % track_id)
        elif u == r and u > p:
            if artist['genres'][0] in urban:
                with open('output/urbantracks.txt', 'a') as f:
                    f.write('spotify:track:%s\r' % track_id)
            elif artist['genres'][0] in rock:
                with open('output/rocktracks.txt', 'a') as f:
                    f.write('spotify:track:%s\r' % track_id)
        elif p == u and u == r:
            if artist['genres'][0] in pop:
                with open('output/poptracks.txt', 'a') as f:
                    f.write('spotify:track:%s\r' % track_id)
            elif artist['genres'][0] in urban:
                with open('output/urbantracks.txt', 'a') as f:
                    f.write('spotify:track:%s\r' % track_id)
            elif artist['genres'][0] in rock:
                with open('output/rocktracks.txt', 'a') as f:
                    f.write('spotify:track:%s\r' % track_id)
        else: # there are no ties, so take the most frequent genre
            bigname = biggest(p, u, r)
            if bigname == 'p':
                with open('output/poptracks.txt', 'a') as f:
                    f.write('spotify:track:%s\r' % track_id)
            elif bigname == 'u':
                with open('output/urbantracks.txt', 'a') as f:
                    f.write('spotify:track:%s\r' % track_id)
            elif bigname == 'r':
                with open('output/rocktracks.txt', 'a') as f:
                    f.write('spotify:track:%s\r' % track_id)

def biggest(p, u, r):
    bigname = 'p'
    big = p
    if u > big:
        bigname = 'u'
        big = u
    if r > big:
        bigname = 'r'
        big = r
    return bigname

def main():
    pop, urban, rock = buildSubgenres()
    genre_set = set()
    for line in fileinput.input(sys.argv[1]):
        track_id = line.strip('http://open.spotify.com/track/').strip()
        artist_id, artist = getArtist(track_id)
        sortGenres(artist_id, pop, urban, rock, track_id)
        # genres = getGenres(artist_id)
        # print artist, genres
        # for g in genres:
        #     genre_set.add(g)
    # sorted_genres = sorted(genre_set, key=lambda item: (int(item.partition(' ')[0]) if item[0].isdigit() else float('inf'), item))
    # print sorted_genres
    # for item in sorted_genres:
    #     print item

if __name__ == "__main__":
    main()
