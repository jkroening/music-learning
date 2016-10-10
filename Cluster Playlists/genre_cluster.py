######################
## sort spotify playlists by spotify genres
## using lists of spotify subgenres
## separated as config files
######################

import spotipy
import fileinput
import sys
import pdb
sys.path.append( "../Modules")
import spotify_methods as sptfy


def buildSubgenres():
    pop, urban, rock = [], [], []
    for line in fileinput.input('config/pop.txt'):
        pop.append(line.strip())
    for line in fileinput.input('config/urban.txt'):
        urban.append(line.strip())
    for line in fileinput.input('config/rock.txt'):
        rock.append(line.strip())
    return pop, urban, rock

def sortGenres(artist_id, pop, urban, rock, track_id, token):
    p, u, r = 0, 0, 0
    genres = sptfy.getArtistGenres(artist_id, token = token)
    if len(genres) < 1:
        with open('../output/unknowntracks.txt', 'a') as f:
            f.write('spotify:track:%s\r' % track_id)
            print "Not found: {}".format(track_id)
    else:
        for g in genres:
            if g in pop:
                p = p + 1
            if g in urban:
                u = u + 1
            if g in rock:
                r = r + 1
        # if there are ties, take the first genre listed of the ties
        if p == u and p > r:
            if genres[0] in pop:
                with open('../output/poptracks.txt', 'a') as f:
                    f.write('spotify:track:%s\r' % track_id)
            elif genres[0] in urban:
                with open('../output/urbantracks.txt', 'a') as f:
                    f.write('spotify:track:%s\r' % track_id)
        elif p == r and p > u:
            if genres[0] in pop:
                with open('../output/poptracks.txt', 'a') as f:
                    f.write('spotify:track:%s\r' % track_id)
            elif genres[0] in rock:
                with open('../output/rocktracks.txt', 'a') as f:
                    f.write('spotify:track:%s\r' % track_id)
        elif u == r and u > p:
            if genres[0] in urban:
                with open('../output/urbantracks.txt', 'a') as f:
                    f.write('spotify:track:%s\r' % track_id)
            elif genres[0] in rock:
                with open('../output/rocktracks.txt', 'a') as f:
                    f.write('spotify:track:%s\r' % track_id)
        elif p == u and u == r:
            if genres[0] in pop:
                with open('../output/poptracks.txt', 'a') as f:
                    f.write('spotify:track:%s\r' % track_id)
            elif genres[0] in urban:
                with open('../output/urbantracks.txt', 'a') as f:
                    f.write('spotify:track:%s\r' % track_id)
            elif genres[0] in rock:
                with open('../output/rocktracks.txt', 'a') as f:
                    f.write('spotify:track:%s\r' % track_id)
        else: # there are no ties, so take the most frequent genre
            bigname = biggest(p, u, r)
            if bigname == 'p':
                with open('../output/poptracks.txt', 'a') as f:
                    f.write('spotify:track:%s\r' % track_id)
            elif bigname == 'u':
                with open('../output/urbantracks.txt', 'a') as f:
                    f.write('spotify:track:%s\r' % track_id)
            elif bigname == 'r':
                with open('../output/rocktracks.txt', 'a') as f:
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

    if len(sys.argv) > 1:
        in_file = sys.argv[1]
    else:
        in_file = "../input/input.txt"

    token = sptfy.authSpotipy()

    for line in fileinput.input(in_file):
        track_id = line.strip('http://open.spotify.com/track/').strip()
        artist_id = sptfy.pullSpotifyTrack(track_id)['spotify_artist_id']
        sortGenres(artist_id, pop, urban, rock, track_id, token)

if __name__ == "__main__":
    main()
