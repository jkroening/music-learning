import subprocess as sp
import os

for fn in os.listdir('in'):
    if fn.endswith(".m4a") or fn.endswith(".mp3"):

        inputfile = "in/%s" % fn
        outputfile = "out/%s" % fn

        cmd = ['ffmpeg', '-i', inputfile, '-vn', '-acodec', 'copy', '-metadata', 'copyright=', outputfile]

        sp.check_call(cmd)
