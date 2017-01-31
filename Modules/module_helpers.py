import requests
import time


def callAPI(url, payload = None):
    try:
        response = requests.get(url, params = payload)
        ## if rate limit is about to be exceeded, wait for one minute so it can reset (~120 requests allowed per minute)
        if "x-ratelimit-remaining" in response.headers and int(response.headers.get('x-ratelimit-remaining')) < 5:
            time.sleep(60)
        ## the following is a Spotify error response check (usually rate limit)
        ## later implementation should authenticate requests so as to increase this limit
        elif "error" in response.json():
            print("Trouble with API call: %s") % url
            time.sleep(5)
            return callAPI(url, payload)
        data = response.json()
    except:
        print("Trouble with API call: %s") % url
        time.sleep(2)
        return callAPI(url, payload)
    return data

def chunker(seq, size):
    return (seq[pos:pos + size] for pos in xrange(0, len(seq), size))

def flattenDict(d):
    def expand(key, value):
        if isinstance(value, dict):
            return [ (key + '.' + k, v) for k, v in flattenDict(value).items() ]
        else:
            if isinstance(value, unicode):
                return [ (key, unidecode(value)) ]
            else:
                return [ (key, value) ]
    items = [ item for k, v in d.items() for item in expand(k, v) ]
    return dict(items)

def flattenDictCustom(d):
    """
    Custom function to flatten a dictionary but not label children keys by parent keys.
    """
    def expand(key, value):
        if isinstance(value, dict):
            return [ (k, v) for k, v in flattenDict(value).items() ]
        else:
            if isinstance(value, unicode):
                return [ (key, unidecode(value)) ]
            else:
                return [ (key, value) ]
    items = [ item for k, v in d.items() for item in expand(k, v) ]
    return dict(items)
