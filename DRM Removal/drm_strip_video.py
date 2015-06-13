import subprocess as sp
import os

for fn in os.listdir('in'):
    if fn.endswith(".m4v") or fn.endswith(".mp4"):

        inputfile = "in/%s" % fn
        outputfile = "out/%s" % fn

        cmd = ['ffmpeg', '-i', inputfile, '-vcodec', 'copy', '-metadata', 'copyright=', outputfile]

        sp.check_call(cmd)
