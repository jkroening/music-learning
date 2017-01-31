######################
## take a txt file export of an iTunes playlist
## and output a list
######################

with open("../input/input.txt", "r") as f:
    outlines = []
    inlines = f.readlines()
    outlines.append('<ol>' + '\n')
    for i in inlines[0:]:
        tabs = []
        for t in i.split('  '):
            if len(t) < 1:
                continue
            else:
                tabs.append(t.strip())
        name = tabs[0]
        artist = tabs[1]
        album = tabs[2]
        print tabs
        if 'Name' == name and 'Artist' == artist:
            continue
        outlines.append('\t<li>' + artist + ' - <em>' + album + '</em></li>\n')
        # if '<br/>' in t.strip():
        #     break
        # elif len(t.strip()) < 1:
        #     pass
        # else:
        #     outlines.append('\t<li>' + t.strip() + '</li>' + '\n')
    outlines.append('</ol>' + '\n')

with open("../output/output.txt", "w") as f:
    f.writelines(outlines)
