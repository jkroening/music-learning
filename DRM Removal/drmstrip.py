import subprocess as sp
import os

for fn in os.listdir('in'):
    if fn.endswith(".m4a") or fn.endswith(".mp3") or fn.endswith(".m4p"):

        inputfile = "in/%s" % fn
        # if fn.endswith(".m4p"):
        #     fn = fn.replace(".m4p", ".m4a")
        outputfile = "out/%s" % fn

        cmd = ['ffmpeg', '-i', inputfile, '-vn', '-acodec', 'copy', '-metadata', 'copyright=', outputfile]

        sp.check_call(cmd)
