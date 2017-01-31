######################
## this script converts text in a wordpress post
## to a portfolio with indents and such
######################

import re

with open("input/input.txt", "r") as f:
    outlines = []
    inlines = f.readlines()
    outlines.append('<div id="col-left">' + \
                    inlines[0].split('<center>')[1].split('<br />')[0] + '\n')
    outlines.append('<a class="btn btn-green" href="' + \
                    inlines[-3].split('href ="')[1].split('">')[0] + \
                    '" target="_blank">Spotify Playlist</a></div>\n')
    outlines.append('<div id="col-right">\n')
    outlines.append('<h2>' + inlines[0].split('<br />')[-1].split('\n')[0] + \
                    '</h2>\n')
    outlines.append('\n')
    outlines.append('<p style="line-height: 0.3em;"></p>\n')
    outlines.append('<ol>' + '\n')
    for t in inlines[4:]:
        if len(t.strip()) < 1:
            outlines.append('</ol>' + '\n')
            outlines.append('</div>')
            break
        if '<br/>' in t.strip():
            outlines.append('</ol>' + '\n')
            outlines.append('</div>')
            break
        elif '</div>' in t.strip():
            outlines.append('</ol>' + '\n')
            outlines.append('</div>')
            break
        elif '</center>' in t.strip():
            outlines.append('</ol>' + '\n')
            outlines.append('</div>')
            break
        else:
            outlines.append('\t<li>' + \
                            re.split('\d+.\s+', t.strip())[-1].lstrip() + \
                            '</li>' + '\n')

writeTextFile(outlines, "../output", "output.txt")
