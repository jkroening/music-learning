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
weights = [1.0, 1.2, 1.0, 1.0, 1.2]
points = [100, 80, 60, 40, 20]

total_pts = sum([ c * w * p for c, w, p in zip(counts, weights, points)])
avg_pts = total_pts / sum(counts)

stdev = np.std(np.repeat([5, 4, 3, 2, 1], counts), ddof = 1)

if stdev == 0: stdev = 0.31
print( 10.76 * ( avg_pts + 0.42 / ( stdev ** 2 ) ) )