######################
## take newline separated text file
## and turn it into a numbered list
######################

with open("../input/input.txt", "r") as f:
    outlines = []
    inlines = f.readlines()
    outlines.append('<ol>' + '\n')
    for t in inlines[0:]:
        if '<br/>' in t.strip():
            break
        elif len(t.strip()) < 1:
            pass
        else:
            outlines.append('\t<li>' + t.title().strip() + '</li>' + '\n')
    outlines.append('</ol>' + '\n')

with open("../output/output.txt", "w") as f:
    f.writelines(outlines)
