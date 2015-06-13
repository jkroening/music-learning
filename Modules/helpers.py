import os
import time
import requests
import pandas as pd

def loadFile(location, filename):
    try:
        with open(os.path.join(location, filename), "U") as f:
            if ".json" in filename:
                infile = json.load(f)
            elif ".csv" in filename:
                infile = pd.io.parsers.read_csv(f)
            elif ".txt" in filename:
                infile = f.readlines()
            else:
                infile = f.read()
    except Exception as e:
        print e
        if ".json" in filename:
            infile = {}
        elif ".csv" in filename:
            infile = pd.DataFrame(index = None, columns = None)
        elif ".txt" in filename:
            infile = []
        else:
            infile = None
    return infile

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