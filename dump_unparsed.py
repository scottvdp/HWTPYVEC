#!/usr/bin/python3.1

"""Utility to dump the string that will be parsed from a vector file"""

import vec
import sys
from vec import vecfile
from vec import pdf

def dump_one(f):
    """Print the string that will be tokenized"""

    (major, minor) = vecfile.ClassifyFile(f)
    if major == "pdf" or (major == "ai" and minor == "pdf"):
        contents = pdf.ReadPDFPageOneContents(f)
    elif major == "eps" or (major == "ai" and minor == "eps"):
        f = open(f, "rU")  # 'U' converts all newline reps to '\n'
        contents = f.read()
    else:
        print("unknown type", major, minor)
        return
    i = contents.find("%%EndSetup")
    if i > 0:
        contents = contents[i:]
    sys.stdout.write(contents)

if __name__ == "__main__":
    dump_one(sys.argv[1])
