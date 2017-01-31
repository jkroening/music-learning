######################
## randomly shuffle a spotify playlist
######################

import sys
import random
sys.path.append( "../Modules")
import helpers as hlpr


def main():

    track_list = hlpr.loadFile("../input", "input.txt")
    random.shuffle(track_list)
    hlpr.writeTextFile(track_list, "../output", "output.txt")


if __name__ == "__main__":
    main()
