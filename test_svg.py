#!/usr/bin/python3.1

import unittest
import vec
from vec import geom
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

class TestImportSVGFile(unittest.TestCase):

  def ParseOneSVG(self, f):
    art = svg.ParseSVGFile("testfiles/" + f)
    if SHOW:
      opt = art2polyarea.ConvertOptions()
      opt.filled_only = False
      opt.smoothness = 3
      pareas = art2polyarea.ArtToPolyAreas(art, opt)
      for pa in pareas.polyareas:
        showfaces.ShowPolyArea(pa, f)

  def testL(self):
    self.ParseOneSVG("L.svg")

  def test3(self):
    self.ParseOneSVG("3.svg")


class TestParseCoordPair(unittest.TestCase):

  def testOnePair(self):
    s = "1.0 -3.5\nX"
    (i, pt) = svg._ParseCoordPair(s, 0)
    self.assertEqual(pt, (1.0, -3.5))
    self.assertEqual(i, len(s) - 1)
    s = "X .6,3"
    (i, pt) = svg._ParseCoordPair(s, 2)
    self.assertEqual(pt, (0.6, 3.0))
    self.assertEqual(i, len(s))
    s = "-.3\n,\r\t-4.25 "
    (i, pt) = svg._ParseCoordPair(s, 0)
    self.assertEqual(pt, (-0.3, -4.25))
    self.assertEqual(i, len(s))

  def testTwoPairs(self):
    s = "0,0 3,4"
    (i, pt1, pt2) = svg._ParseTwoCoordPairs(s, 0)
    self.assertEqual(pt1, (0.0, 0.0))
    self.assertEqual(pt2, (3.0, 4.0))

  def testThreePairs(self):
    s = "-1.0 , -3.0 , 4, 5, -6.0 7.0  "
    (i, pt1, pt2, pt3) = svg._ParseThreeCoordPairs(s, 0)
    self.assertEqual(pt1, (-1.0, -3.0))
    self.assertEqual(pt2, (4.0, 5.0))
    self.assertEqual(pt3, (-6.0, 7.0))
    self.assertEqual(i, len(s))

  def testParsePairList(self):
    s = "1,2 3,4 5,6 7,8 9,10"
    pts = svg._ParseCoordPairList(s)
    self.assertEqual(pts, [(1.0,2.0), (3.0,4.0), (5.0, 6.0),
        (7.0, 8.0), (9.0, 10.0)])


class TestPaint(unittest.TestCase):

  def testParsePaint(self):
    p = svg._ParsePaint("#1200FF")
    self.assertEqual(p.color, (18.0/255.0, 0.0, 1.0))
    p = svg._ParsePaint("yellow")
    self.assertEqual(p.color, (1.0, 1.0, 0.0))


class TestPaths(unittest.TestCase):

  def testParseLineSubpaths(self):
    gs = svg._SState()
    z = (0.0, 0.0)
    (i, sp, endpt) = svg._ParseSubpath("M 0.0 0.0 L 1.0 2.0", 0, z, gs)
    self.assertEqual(sp.closed, False)
    self.assertEqual(sp.segments, [('L', (0.0,0.0), (1.0,2.0))])
    (i, sp, endpt) = svg._ParseSubpath( \
      "M 2.000 -1.000 L 2.000 1.000 L 0.000 1.000 L 2.000 -1.000 Z",
      0, (10.0, 20.0), gs)
    self.assertEqual(sp.closed, True)
    self.assertEqual(sp.segments,
      [('L', (2.0, -1.0), (2.0, 1.0)), ('L', (2.0, 1.0), (0.0, 1.0)),
       ('L', (0.0, 1.0), (2.0, -1.0))])
    self.assertEqual(endpt, (2.0, -1.0))
    (i, sp, endpt) = svg._ParseSubpath("m 1.0 0.0 l 2.0 3.0", 0, (5.0, 6.0), gs)
    self.assertEqual(sp.segments, [('L', (6.0, 6.0), (8.0, 9.0))])

  def testParseCurveSubpaths(self):
    gs = svg._SState()
    z = (0.0, 0.0)
    (i, sp, _) = svg._ParseSubpath("M 0 0 C 1,1 2,1 0,3", 0, z, gs)
    self.assertEqual(sp.segments, [('B', (0.0, 0.0), (0.0, 3.0), (1.0, 1.0), (2.0, 1.0))])



if __name__ == "__main__":
  unittest.main()
