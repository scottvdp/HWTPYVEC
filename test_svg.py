#!/usr/bin/python3.1

import unittest
import vec
from vec import vecfile
from vec import art2polyarea
from vec import svg
from vec import showfaces

SHOW = True  # should we show graphic plots of tested files?

def DumpArt(art):
  print("ART")
  for p in art.paths:
    print("path; filled=", p.filled, "fillpaint=", p.fillpaint.color)
    for sp in p.subpaths:
      print(sp.segments)

class TestImporSVGFile(unittest.TestCase):

  def ParseOneSVG(self, f):
    art = svg.ParseSVGFile("testfiles/" + f)
    if SHOW:
      opt = art2polyarea.ConvertOptions()
      pareas = art2polyarea.ArtToPolyAreas(art, opt)
      for pa in pareas.polyareas:
        showfaces.ShowPolyArea(pa, f)

  def testL(self):
    self.ParseOneSVG("L.svg")

  def test3(self):
    self.ParseOneSVG("3.svg")


if __name__ == "__main__":
  unittest.main()
