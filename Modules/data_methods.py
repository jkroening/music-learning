from sklearn import decomposition
from sklearn import preprocessing
from sklearn import cluster
import pandas as pd
import numpy as np
import chart_studio.plotly as py
import sys
from plotly.graph_objs import *
import pdb


def transformPCA(X, n):
    pca = decomposition.PCA(n_components = n)
    X = pca.fit_transform(X)
    return X

def centerScaleData(X):
    standard_scaler = preprocessing.StandardScaler()
    X = standard_scaler.fit_transform(X)
    return X

def minMaxScaleData(X):
    minmax_scaler = preprocessing.MinMaxScaler()
    X = minmax_scaler.fit_transform(X)
    return X

def classifyUnsupervised(X, n_clusters = 6, method = "km", random_state = 42):
    if method == "km":
        clf = cluster.KMeans(init = "random", n_clusters = n_clusters, random_state = random_state)
        clusters = clf.fit_predict(X).tolist()
    return clusters

def scatterplot(data, filename, title = "", xAxisLabel = "", yAxisLabel = ""):
    trace1 = Scatter(
        x = data[ : , 0],
        y = data[ : , 1],
        mode = "markers"
    )
    layout = Layout(
        title = title,
        xaxis = XAxis(
            title = xAxisLabel,
            showgrid = False,
            zeroline = False
        ),
        yaxis = YAxis(
            title = yAxisLabel,
            showline = False
        )
    )
    data = Data([trace1])
    fig = Figure(data = data, layout = layout)
    plot_url = py.plot(fig, filename = filename)

def closest(X, p):
    disp = X - p
    return np.argmin((disp * disp).sum(1))

def distances(X, p):
    disp = X - p
    return (disp * disp).sum(1)

## take pandas dataframe and reorder by distance from point p in distances()
def sortByDistance(df, dist):
    df = df.reset_index()
    return df.iloc[np.argsort(dist), ]

def expandToPoints(X, df, artist, title):
    try:
        start = np.where((df.artist.str.lower() == artist.lower()) & \
                         (df.title.str.lower() == title.lower()))[0][0]
    except:
        print("Artist name and Song title not found as entered...")
        print("Please try again.")
        sys.exit()
    ds = distances(X, X[start, : ])
    dfs = sortByDistance(df, ds)
    return dfs

def walkPoints(X, df, artist, title):
    try:
        start = np.where((df.artist.str.lower() == artist.lower()) & \
                         (df.title.str.lower() == title.lower()))[0][0]
    except:
        print("Artist name and Song title not found as entered...")
        print("Please try again.")
        sys.exit()
    out_list = ["spotify:track:%s" % df.iloc[start].spotify_id]
    curr_point = X[start, : ].copy()
    ## once the point has been touched, make the value impossiblly far away
    X[start, : ] = np.repeat(10e9, X.shape[1])
    for i in range(X.shape[0] - 1):
        nxt = closest(X, curr_point)
        next_point = X[nxt, : ].copy()
        if 'local' in df.iloc[nxt].spotify_id:
            out_list.append(df.iloc[nxt].spotify_id)
        else:
            out_list.append("spotify:track:%s" % df.iloc[nxt].spotify_id)
        X[nxt, : ] = np.repeat(10e9, X.shape[1])
        curr_point = next_point
    return out_list

def getSimilarPoints(X, df, artist, title, n = 5, stdout = True):
    dfs = expandToPoints(X, df, artist, title)
    neighbors = dfs[1:n + 1][['artist', 'title']]
    if stdout:
        return neighbors
    else:
        return dfs[1:n + 1]
