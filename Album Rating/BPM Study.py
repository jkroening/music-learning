
import xml.etree.ElementTree as ET
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from bs4 import BeautifulSoup
import pdb

## be sure to manually strip the xml down to the dict right following plist
## ie. eliminate the plist tag and any metadata at the bottom of the file after the tracks
with open("BPM Study.xml") as f:
    root = ET.fromstring(f.read())

lengths = []
for node in root:
    lengths.append(len(node))

max_len = max(lengths)

colnames = []
for node in root:
    if len(node) == max_len:
        for child in node:
            if child.tag == 'key':
                colnames.append(child.text)

nodes = []
for node in root:
    if len(node) == 0:
        continue
    else:
        row_dict = dict()
        for child in node:
            if child.tag == 'key':
                key = child.text
            else:
                val = child.text
                row_dict[key] = val
            nodes.append(row_dict)

df = pd.DataFrame(nodes)
df = df.drop_duplicates()
df_albums = df.drop_duplicates(['Artist', 'Album'])

ratings = pd.to_numeric(df.Rating)
ratings_distrib = ratings.value_counts()
ratings_mu = np.mean(ratings)
ratings_sd = np.std(ratings)

def score(x):
    x = x.astype(float)
    if sum(x) == len(x):
        return 1.0
    mean_album = np.mean(x)
    print mean_album
    sd_album = np.std(x, ddof = 1)
    if sd_album == 0:
        sd_album = 0.25
    print sd_album
    x[x == 4] = 4 * 1.2
    x[x == 2] = 2 * 1.2
    print x
    adj_mean = np.mean(x[x != 3])
    if np.isnan(adj_mean):
        adj_mean = 3.00
    print adj_mean
    prop_4or5 = len(x[x > 3]) / (len(x) * 1.0)
    print prop_4or5
    adj1 = (adj_mean - 3) * prop_4or5
    print(adj1)
    adj2 = adj1 + len(x[x >= 3]) * 0.03
    print adj2
    score = mean_album + adj2
    print score
    if prop_4or5 == 0:
        sd_adj = sd_album * 0.05
    else:
        sd_adj = sd_album * prop_4or5 / (len(x) * 1.0)
    print sd_adj
    out = score - sd_adj
    return out

def scale(x, max = 5.662521, min = 1.0):
    return ((x - min) / (max - min))

means = []
scores = []
for a in np.unique(df_albums.Album):
    ratings = df.Rating[df.Album == a].astype(float) / 20
    s = score(ratings)
    scaled = scale(s)
    print a
    print s
    print scaled
    means.append(np.mean(ratings))
    scores.append(scaled)

bpms = df_albums['BPM']
bpms = bpms.astype(float).values
bpms[np.isnan(bpms)] = 0

plt.hist(means)
plt.show()

def transform(x):
    score = -1 * (7**(-1 * x))
    return score

print min(scores)
print max(scores)
plt.hist(scores)
plt.show()
transformed = np.fromiter((transform(b) for b in scores), float)
transformed = np.fromiter((scale(t, max(transformed), min(transformed)) * 100 for t in transformed), float)
print min(transformed)
print max(transformed)
plt.hist(transformed, bins = 20)
plt.show()

plt.scatter(scores, transformed, alpha = 0.5)
plt.xlim([0, 1.05])
plt.ylim([0, 105.0])
plt.show()
