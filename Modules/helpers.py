import os
import time
import csv
import requests
import pandas as pd
from unidecode import unidecode

def loadFile(location, filename, as_dict = False):
    try:
        with open(os.path.join(location, filename), "U") as f:
            if ".json" in filename:
                infile = json.load(f)
            elif ".csv" in filename and not as_dict:
                infile = pd.io.parsers.read_csv(f)
            elif ".csv" in filename and as_dict:
                reader = csv.reader(f)
                infile = {}
                for row in reader:
                    infile[row[0]] = row[1]
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

def writeTextFile(data, location, filename):
    with open(os.path.join(location, filename), "w") as f:
        for line in data:
            f.write("%s\n" % line)

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