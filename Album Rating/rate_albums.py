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
import spotify_methods as sp
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
    
    rating = 0
    for ls in [ones, twos, threes, fours, fives]:
        ## playlists are looped in this order such that if a song is in multiple lists it's rating will end up being the highest one
        rating = rating + 1
        for song in ls:
            track_id, spotify_uri = sp.getSpotifyTrackIDs(song)
            if not lookupSongBySpotifyID(track_id, db):
                track = sp.pullSpotifyTrack(track_id)
                db = db.append([{'spotify_id' : track_id, 'artist' : track['artist'], 'album' : track['album'], 'spotify_album_id' : track['spotify_album_id'], 'song' : track['title'], 'rating' : rating}])

    db = db.sort(['artist', 'album', 'rating'])
    saveDataFrame(db, "../Databases", "song_ratings_db.csv")

    for album in pd.unique(zip(db.artist, db.album)):
        artist = album[0]
        album = album[1]
        if not lookupAlbumBySpotifyID(album, album_ratings):
            album_id = pd.unique(db[db.artist == artist][db.album == album]['spotify_album_id'])[0]
            album_data = sp.pullSpotifyAlbum(album_id)
            ratings = db[db.artist == artist][db.album == album]['rating'].tolist()
            if len(ratings) < 3:
                ## don't make album ratings for singles
                continue
            score = 0
            for r in ratings:
                if r == 5:
                    score = score + 100 * 1.0
                elif r == 4:
                    score = score + 80 * 1.2
                elif r == 3:
                    score = score + 60 * 1.0
                elif r == 2:
                    score = score + 40 * 1.0
                elif r == 1:
                    score = score + 20 * 1.2
            std = np.std(ratings)
            if std == 0.0:
                std = 0.31
            avg = (score / len(ratings)) + 0.42 / (std ** 2.0)
            album_score = avg * 10.76 ## scaling applied to set ceiling album "OK Computer" at 1000 points
            if album_score >= 875:
                album_rating = 5.0`
            elif album_score >= 825:
                album_rating = 4.5
            elif album_score >= 700:
                album_rating = 4.0
            elif album_score >= 640:
                album_rating = 3.5
            elif album_score >= 530:
                album_rating = 3.0
            elif album_score >= 430:
                album_rating = 2.5
            elif album_score > 375:
                album_rating = 2.0
            elif album_score > 350:
                album_rating = 1.5
            elif album_score > 250:
                album_rating = 1.0
            elif album_score <= 250:
                album_rating = 0.5
            album_ratings = album_ratings.append([{'spotify_album_id' : album_id, 'artist' : artist, 'album' : album, 'year' : album_data['year'], 'album_rating' : album_rating, 'album_score' : album_score}])

    saveDataFrame(album_ratings, "../Databases", "album_ratings_db.csv")


if __name__ == "__main__":
    main()