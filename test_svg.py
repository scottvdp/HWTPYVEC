#!/usr/bin/python3.1

import unittest
import vec
import xml.dom.minidom
from vec import geom
from vec import vecfile
from vec import art2polyarea
from vec import svg
from vec import showfaces

SHOW = False  # should we show graphic plots of tested files?

def DumpArt(art):
  print("ART")
  for p in art.paths:
    print("path; filled=", p.filled, "fillpaint=", p.fillpaint.color,
        "stroked=", p.stroked, "strokepaint=", p.strokepaint.color)
    for sp in p.subpaths:
      print(sp.segments)


def GetNode(s):
  doc = xml.dom.minidom.parseString(s)
  return doc.firstChild


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
    p = svg._ParsePaint("url(#g)")
    self.assertEqual(p.color, geom.black_paint.color)


class TestLength(unittest.TestCase):

  def testParseLength(self):
    gs = svg._SState()
    gs.dpi = 200
    (i, v) = svg._ParseLength("11", gs, 0)
    self.assertEqual(v, 11.0)
    (i, v) = svg._ParseLength("-3.5 px", gs, 0)
    self.assertEqual(v, -3.5)
    self.assertEqual(i, len("-3.5 px"))
    (i, v) = svg._ParseLength("3in", gs, 0)
    self.assertEqual(v, 600.0)


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
    (i, sp, _) = svg._ParseSubpath("m 1.0 0 h 3.5 v 2.0", 0, z, gs)
    self.assertEqual(sp.segments, [('L', (1.0, 0.0), (4.5, 0.0)),
        ('L', (4.5, 0.0), (4.5, 2.0))])

  def testParseCurveSubpaths(self):
    gs = svg._SState()
    z = (0.0, 0.0)
    (i, sp, _) = svg._ParseSubpath("M 0 0 C 1,1 2,1 0,3", 0, z, gs)
    self.assertEqual(sp.segments, [('B', (0.0, 0.0), (0.0, 3.0), (1.0, 1.0), (2.0, 1.0))])
    (i, sp, _) = svg._ParseSubpath("M0 0 C  1,1 2,1 0,3 S 4,5 6,7", 0, z, gs)
    self.assertEqual(len(sp.segments), 2)

  def testArcSubpaths(self):
    gs = svg._SState()
    z = (0.0, 0.0)
    (i, sp, _) = svg._ParseSubpath("M 0 0 A10,10 30 0 1 8.0 9.5", 0, z, gs)
    self.assertEqual(sp.segments, [('A', (0.0, 0.0), (8.0, 9.5),
        (10.0, 10.0), 30.0, False, True)])


class TestRect(unittest.TestCase):

  def testProcessRect(self):
    gs = svg._SState()
    art = geom.Art()
    s = '<rect x="1" y="1" width="100" height="200" fill="none" stroke="blue"/>'
    svg._ProcessRect(GetNode(s), art, gs)
    self.assertEqual(art.paths[0].subpaths[0].segments,
      [('L', (1.0, 1.0), (101.0, 1.0)), ('L', (101.0, 1.0), (101.0, 201.0)),
       ('L', (101.0, 201.0), (1.0, 201.0)), ('L', (1.0, 201.0), (1.0, 1.0))])
    s = '<rect width="10" height="10" rx="2" fill="black"/>'
    art = geom.Art()
    svg._ProcessRect(GetNode(s), art, gs)
    self.assertEqual(art.paths[0].subpaths[0].segments,
      [('L', (2.0, 0.0), (8.0, 0.0)), ('A', (8.0, 0.0), (10.0, 2.0), (2.0, 2.0), 0.0, False, False),
       ('L', (10.0, 2.0), (10.0, 8.0)), ('A', (10.0, 8.0), (8.0, 10.0), (2.0, 2.0), 0.0, False, False),
       ('L', (8.0, 10.0), (2.0, 10.0)), ('A', (2.0, 10.0), (0.0, 8.0), (2.0, 2.0), 0.0, False, False),
       ('L', (0.0, 8.0), (0.0, 2.0)), ('A', (0.0, 2.0), (2.0, 0.0), (2.0, 2.0), 0.0, False, False)])


class TestCircle(unittest.TestCase):

  def testProcessCircle(self):
    gs = svg._SState()
    art = geom.Art()
    s = '<circle cx="600" cy="200" r="100" fill="red"/>'
    svg._ProcessCircle(GetNode(s), art, gs)
    self.assertEqual(art.paths[0].subpaths[0].segments,
      [('A', (700.0, 200.0), (600.0, 300.0), (100.0, 100.0), 0.0, False, False),
       ('A', (600.0, 300.0), (500.0, 200.0), (100.0, 100.0), 0.0, False, False),
       ('A', (500.0, 200.0), (600.0, 100.0), (100.0, 100.0), 0.0, False, False),
       ('A', (600.0, 100.0), (700.0, 200.0), (100.0, 100.0), 0.0, False, False)])
    self.assertEqual(art.paths[0].filled, True)
    self.assertEqual(art.paths[0].fillpaint.color, (1.0, 0.0, 0.0))


class Ellipse(unittest.TestCase):

  def testProcessEllipse(self):
    gs = svg._SState()
    art = geom.Art()
    s = '<ellipse cx="10" cy="20" rx="100px" ry="50px" fill="black"/>'
    svg._ProcessEllipse(GetNode(s), art, gs)
    self.assertEqual(art.paths[0].subpaths[0].segments,
      [('A', (110.0, 20.0), (10.0, 70.0), (100.0, 50.0), 0.0, False, False),
       ('A', (10.0, 70.0), (-90.0, 20.0), (100.0, 50.0), 0.0, False, False),
       ('A', (-90.0, 20.0), (10.0, -30.0), (100.0, 50.0), 0.0, False, False),
       ('A', (10.0, -30.0), (110.0, 20.0), (100.0, 50.0), 0.0, False, False)])


if __name__ == "__main__":
  unittest.main()
