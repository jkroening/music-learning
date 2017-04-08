######################
## take playlists of songs rated 5, 4, 3, 2, and 1
## and using a weighted rating system
## give each album an overall rating
######################

import os
import sys
import pdb
import pandas as pd
import numpy as np
sys.path.append( "../Modules")
from helpers import loadFile
import spotify_methods as sptfy
from db_methods import lookupSongBySpotifyID, lookupAlbumBySpotifyID, saveDataFrame

def main():

    # ## load tracks in playlist
    fives = loadFile("input", "fives.txt")
    fours = loadFile("input", "fours.txt")
    threes = loadFile("input", "threes.txt")
    twos = loadFile("input", "twos.txt")
    ones = loadFile("input", "ones.txt")

    ## load database of song ratings
    db = loadFile("../Databases", "song_ratings_db.csv")
    album_ratings = loadFile("../Databases", "album_ratings_db.csv")

    config = loadFile("../config", "config.csv", True)
    token = sptfy.authSpotipy()

    rating = 0
    for ls in [ones, twos, threes, fours, fives]:
        ## playlists are looped in this order such that if a song is in multiple lists it's rating will end up being the highest one
        rating = rating + 1
        for song in ls:
            track_id, spotify_uri = sptfy.getSpotifyTrackIDs(song)
            if not lookupSongBySpotifyID(track_id, db):
                track = sptfy.pullSpotifyTrack(track_id, token = token)
                db = db.append([{'spotify_id' : track_id, 'artist' : track['artist'], 'album' : track['album'], 'spotify_album_id' : track['spotify_album_id'], 'song' : track['title'], 'rating' : rating}])

    db = db.sort(['artist', 'album', 'rating'])
    saveDataFrame(db, "../Databases", "song_ratings_db.csv")

    for album in pd.unique(zip(db.artist, db.album)):
        artist = album[0]
        album = album[1]
        if not lookupAlbumBySpotifyID(album, album_ratings):
            album_id = pd.unique(db[db.artist == artist][db.album == album]['spotify_album_id'])[0]
            album_data = sptfy.pullSpotifyAlbum(album_id, token = token)
            ratings = db[db.artist == artist][db.album == album]['rating'].tolist()
            if len(ratings) < 3:
                ## don't make album ratings for singles
                continue
            score = 0
            countNot3 = len(np.where(r != 3))
            countMoreThan2 = len(np.where(r > 2))
            countMoreThan3 = len(np.where(r > 3))
            for r in ratings:
                if r == 5:
                    score = score + 100 * 1.0
                    scoreNot3 = score + 100 * 1.0
                elif r == 4:
                    score = score + 80 * 1.2
                    scoreNot3 = score + 80 * 1.2
                elif r == 3:
                    score = score + 60 * 1.0
                elif r == 2:
                    score = score + 40 * 1.2
                    scoreNot3 = score + 40 * 1.2
                elif r == 1:
                    score = score + 20 * 1.0
                    scoreNot3 = score + 20 * 1.0
            std = np.std(ratings)
            if std == 0.0:
                std = 0.25

            if countNot3 == 0:
                adjMean = 3
            else:
                adjMean = scoreNot3 / countNot3
            prop4or5 = countMoreThan3 / len(r)
            adj1 = (adjMean - 3) * prop4or5
            adj2 = adj1 + countMoreThan2 * 0.03

            score = np.mean(ratings) + adj2

            if prop4or5 == 0:
                adjSD = std * 0.05
            else:
                adjSD = std * prop4or5 / len(r)

            score = score - adjSD

            ## min possible score: (mean of 1-star)
            min1 = 1.0
            ## max possible score: Radiohead "OK Computer"
            max1 = 5.662521
            min2 = -1.0
            max2 = -0.125

            scaledScore = (score - min1) / (max1 - min1)
            ## transform (curves the linear scores to inflate higher scores and reduce lower)
            transformedScore = -1 * (8 ^ (-1 * scaledScore))
            scaledScore = (transformedScore - min2) / (max2 - min2)
            album_score = (round (scaledScore * 1000)) / 1.0

            if album_score > 1000:
	        album_score = 1000

            if album_score >= 965:
                album_rating = 5.0
            elif album_score >= 890:
                album_rating = 4.5
            elif album_score >= 750:
                album_rating = 4.0
            elif album_score >= 690:
                album_rating = 3.5
            elif album_score >= 625:
                album_rating = 3.0
            elif album_score >= 420:
                album_rating = 2.5
            elif album_score > 325:
                album_rating = 2.0
            elif album_score > 235:
                album_rating = 1.5
            elif album_score >= 100:
                album_rating = 1.0
            elif album_score < 100:
                album_rating = 0.5
            album_ratings = album_ratings.append([{'spotify_album_id' : album_id, 'artist' : artist, 'album' : album, 'year' : album_data['year'], 'album_rating' : album_rating, 'album_score' : album_score}])

    saveDataFrame(album_ratings, "../Databases", "album_ratings_db.csv")


if __name__ == "__main__":
    main()
