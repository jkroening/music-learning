######################
## randomly shuffle a spotify playlist
######################

import sys
import random
import fileinput

def main():
    track_list = []
    for line in fileinput.input('tracks.txt'):
        track_list.append(line.strip())
    random.shuffle(track_list)
    for item in track_list:
        print item

if __name__ == "__main__":
    main()
