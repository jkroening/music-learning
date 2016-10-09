######################
## rate an album using custom scoring system
## based on the ratings of the individual tracks
## NOTE: this is a weighted scoring rater
######################

from __future__ import division
import numpy as np

fives = float(raw_input("How many songs on the album are 5 stars?"))
fours = float(raw_input("How many songs on the album are 4 stars?"))
threes = float(raw_input("How many songs on the album are 3 stars?"))
twos = float(raw_input("How many songs on the album are 2 stars?"))
ones = float(raw_input("How many songs on the album are 1 stars?"))

counts = [fives, fours, threes, twos, ones]
countsNot3 = [fives, fours, twos, ones]
weights = [1.0, 1.2, 1.0, 1.2, 1.0]
weightsNot3 = [1.0, 1.2, 1.2, 1.0]
points = [100, 80, 60, 40, 20]
pointsNot3 = [100, 80, 40, 20]

total_pts = sum([ c * w * p for c, w, p in zip(counts, weights, points)])
avg_pts = total_pts / sum(counts)
score_not_3 = sum([ c * w * p for c, w, p in zip(countsNot3, weightsNot3, pointsNot3)]

stdev = np.std(np.repeat([5, 4, 3, 2, 1], counts), ddof = 1)

if stdev == 0: stdev = 0.25

if sum(countsNot3) == 0:
    adjMean = 3
else:
    adjMean = score_not_3 / sum(countsNot3)
prop4or5 = (fours + fives) / sum(counts)
adj1 = (adjMean - 3) * prop4or5
adj2 = adj1 + (threes + fours + fives) * 0.03

score = (total_pts) / sum(counts) + adj2

if prop4or5 == 0:
    adjSD = stdev * 0.05
else:
    adjSD = stdev * prop4or5 / sum(counts)

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

print "%s :: %s" % (album_score, album_rating)
