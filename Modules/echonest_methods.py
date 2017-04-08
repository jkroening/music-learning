## THIS MODULE IS DEPRECATED
## since Echo Nest was purchased by Spotify

# import sys
# sys.path.append( "../Modules")
import spotify_methods as sptfy
from fuzzywuzzy import fuzz
import pdb
import module_helpers as mhlpr

def pullEchoNestSong(auth, track, album = None, local_link = None):
    url_base = "https://api.spotify.com/v1/audio-features/"

    if 'spotify' in track:
        track_id, spotify_uri = sptfy.getSpotifyTrackIDs(track)

        ## due to echonest using 2 different bucket params and url encoding the ampersand, payload cannot be used
        # payload = {'api_key' : api_key, 'track_id' : spotify_uri, 'bucket' : "audio_summary&bucket=id:spotify", 'format' : "json"}
        url_suffix = "%s" % sptfy.stripSpotifyURI(spotify_uri)
    else:
        pdb.set_trace()
        ## it's an echonest id and can be accessed directly
        url_suffix = "?api_key=%s&id=%s&bucket=audio_summary&bucket=id:spotify&format=json" % (auth, track)

    url = url_base + url_suffix
    data = mhlpr.callAPI(url, headers = auth)

    ## if response is a success
    if int(data['response']['status']['code']) == 0 and len(data['response']['songs']) > 0:
        song = mhlpr.flattenDictCustom(data['response']['songs'][0])
        if 'spotify' in track:
            track = sptfy.pullSpotifyTrack(track_id)
            song['album'] = track['album']
            song['spotify_artist_id'] = track['spotify_artist_id']
            ## add spotify uri to song data
            song['spotify_id'] = track_id
        else:
            song['album'] = album
            song['spotify_id'] = local_link.strip()
        ## pop off unneeded data and flatten dict
        song.pop('audio_md5', None)
        song.pop('analysis_url', None)
        song['echonest_artist_id'] = song.pop('artist_id')
        if 'artist_foreign_ids' in song:
            song.pop('artist_foreign_ids')
        ## rename keys as necessary
        song['echonest_id'] = song.pop('id')
        song['artist'] = song.pop('artist_name')
    elif int(data['response']['status']['code']) == 5:
        ## the song cannot be found by the spotify id
        url = "http://developer.echonest.com/api/v4/song/search"
        if 'spotify' in track:
            track = sptfy.pullSpotifyTrack(track_id)
        artist = track['artist']
        title = track['title']
        payload = {'api_key' : api_key, 'artist' : artist, 'title' : title, 'bucket' : "audio_summary", 'format' : "json"}
        data = mhlpr.callAPI(url, payload)
        if len(data['response']['songs']) > 0:
            ## pop off unneeded data and flatten dict
            song = mhlpr.flattenDictCustom(data['response']['songs'][0])
            if 'spotify' in track:
                song['album'] = track['album']
                song['spotify_artist_id'] = track['spotify_artist_id']
                ## check to be sure it's the correct song -- fuzzy string match of at least .75 levenshtein ratio
                if fuzzyMatch(song['artist'], track['artist'], song['title'], track['title']):
                    song.pop('audio_md5', None)
                    song.pop('analysis_url', None)
                    song['echonest_artist_id'] = song.pop('artist_id')
                    if 'artist_foreign_ids' in song:
                        song.pop('artist_foreign_ids')
                    ## add spotify uri to song data
                    song['spotify_id'] = track_id
                    ## rename keys as necessary
                    song['echonest_id'] = song.pop('id')
                    song['artist'] = song.pop('artist_name')
            else:
                ## pop off unneeded data and flatten dict
                song.pop('audio_md5', None)
                song.pop('analysis_url', None)
                song['echonest_artist_id'] = song.pop('artist_id')
                if 'artist_foreign_ids' in song:
                    song.pop('artist_foreign_ids')
                ## rename keys as necessary
                song['echonest_id'] = song.pop('id')
                song['album'] = album
                song['spotify_id'] = track_id
                song['artist'] = song.pop('artist_name')
        else:
            print "Song not found via EchoNest search: {}".format(spotify_uri)
            return None
    else:
        pdb.set_trace()
        "Unrecognized error code."

    return song

def pullEchoNestArtistTerms(api_key, artist, related_artists = None, related_artist_index = 0, term_min = 0):
    """
    Function to get artist terms and their weights and frequencies.

    @param  related_artists:  artists related to artist, if None, then the terms being gathered are for the artist and not a related artist
    @param  related_artist_index:  the index of the current related artist being evaluated as a terms proxy for the artist
    @param  term_min:  the minimum number of terms that is permitted.
                                   for related_artists this is usually set to 3 to safe-guard against gathering terms from a lesser-known related artist
    """

    url = "http://developer.echonest.com/api/v4/artist/terms"

    spotify_uri = "spotify:artist:%s" % artist['spotify_artist_id']
    payload = {'api_key' : api_key, 'id' : spotify_uri, 'format' : "json"}

    data = mhlpr.callAPI(url, payload)

    # get terms from json
    terms = data['response']['terms']
    if len(terms) > term_min:
        for term in terms:
            term_freq, term_wt, freq, wt = getTermStats(term)
            ## frequency as metric
            artist[term_freq] = freq
            ## frequency * weight as metric
            term_freqwt = "%swt" % term_freq
            artist[term_freqwt] = freq * wt
            ## weight as metric
            artist[term_wt] = wt
        return artist
    else:
        # there are no terms for this artist
        # so search for related artists and get their terms
        if related_artists is None:
            url = "https://api.spotify.com/v1/artists/%s/related-artists" % artist['spotify_artist_id']

            spotify_data = mhlpr.callAPI(url)

            related_artists = spotify_data['artists']
            related_artist_id = {'spotify_artist_id' : sptfy.stripSpotifyURI(related_artists[0]['uri'])}
        else:
            related_artist_id = {'spotify_artist_id' : sptfy.stripSpotifyURI(related_artists[related_artist_index]['uri'])}

        return pullEchoNestArtistTerms(api_key, related_artist_id, related_artists, int(related_artist_index + 1), 3)

def searchEchoNestSong(spotipy, link):
    artist, title, album = sptfy.formatLocalTrack(link)
    url = "http://developer.echonest.com/api/v4/song/search"
    payload = {'api_key' : api_key, 'format' : 'json', 'artist' : artist, 'title' : title}

    data = mhlpr.callAPI(url, payload)

    if len(data['response']['songs']) < 1:
        title = title.split(" (")[0]
        payload = {'api_key' : api_key, 'format' : 'json', 'artist' : artist, 'title' : title}
        data = mhlpr.callAPI(url, payload)
    if len(data['response']['songs']) > 0:
        result = data['response']['songs'][0]
        if fuzzyMatch(artist, result['artist_name'], title, result['title']):
            song_id = result['id']
            return pullEchoNestSong(api_key, song_id, album, link)
    print artist + " -  " + title + " not found in EchoNest search."
    return None

def fuzzyMatch(artist_a, title_a, artist_b, title_b, artist_ratio = 0.90, title_ratio = 0.75):
    ## check to be sure it's the correct song -- fuzzy string match of at least .75 levenshtein ratio
        if fuzz.ratio(title_a.lower(), title_b.lower()) >= title_ratio and fuzz.ratio(artist_a.lower(), artist_b.lower()) >= artist_ratio:
            return True
        else:
            return False

def getTermStats(term):
    term_freq = "%s_freq" % term['name'].replace(" ", "_")
    term_wt = "%s_wt" % term['name'].replace(" ", "_")
    freq = term['frequency']
    wt = term['weight']
    return term_freq, term_wt, freq, wt
