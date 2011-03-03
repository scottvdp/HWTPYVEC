#!/usr/bin/python3.1

"""Unit tests for art2polyarea module."""

import unittest
import vec
from vec import art2polyarea
from vec import geom
from vec import vecfile


class TestClassifyPathPairs(unittest.TestCase):

  def runTest(self):
    pts = geom.Points([(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0),
            (0.2, 0.2), (1.1, 0.1), (0.8, 0.5)])
    a = geom.PolyArea(pts, [0, 1, 2, 3])
    b = geom.PolyArea(pts, [4, 5, 2, 6])
    ans = art2polyarea._ClassifyPathPairs(a, b)
    self.assertEqual(ans, (2, 1))
    ans = art2polyarea._ClassifyPathPairs(b, a)
    self.assertEqual(ans, (0, 1))


class TestBezier3Approx(unittest.TestCase):

  def runTest(self):
    art = vecfile.Art()
    cps = [(0.0, 0.0), (1.0, 1.0), (2.0, 3.0), (3.0, 0.0)]
    ans = art2polyarea.Bezier3Approx(cps, 0)
    self.assertEqual(ans, [cps[0], cps[3]])
    ans = art2polyarea.Bezier3Approx(cps, 1)
    self.assertEqual(len(ans), 3)
    self.assertAlmostEqual(ans[1][0], 1.5)
    self.assertAlmostEqual(ans[1][1], 1.5)
    ans = art2polyarea.Bezier3Approx(cps, 2)
    self.assertEqual(len(ans), 5)
    self.assertAlmostEqual(ans[1][0], 0.75)
    self.assertAlmostEqual(ans[1][1], 0.84375)


class TestCombineSimplePolyAreas(unittest.TestCase):

  def runTest(self):
    # pa0 is square, containing triangles pa1 and pa2
    # pa3 is triangle outside them all
    pa0 = geom.PolyArea(geom.Points( [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]),
        [0, 3, 2, 1])
    pa1 = geom.PolyArea(geom.Points([(0.2, 0.2), (0.8, 0.2), (0.5, 0.5)]),
        [0, 1, 2])
    pa2 = geom.PolyArea(geom.Points([(0.3, 0.6), (0.7, 0.6), (0.5, 0.9)]),
        [0, 1, 2])
    pa3 = geom.PolyArea(geom.Points([(2.0, 0.0), (3.0, 0.0), (3.0, 1.0)]),
        [0, 1, 2])
    ans = art2polyarea.CombineSimplePolyAreas([pa0, pa1, pa2, pa3])
    self.assertEqual(len(ans), 2)
    a1 = ans[0]
    a2 = ans[1]
    self.assertEqual(a1.points.pos,
        [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0),
        (0.2, 0.2), (0.8, 0.2), (0.5, 0.5),
        (0.3, 0.6), (0.7, 0.6), (0.5, 0.9)])
    self.assertEqual(a1.poly, [0, 3, 2, 1])
    self.assertEqual(len(a1.holes), 2)
    self.assertIn([6, 5, 4], a1.holes)
    self.assertIn([9, 8, 7], a1.holes)
    self.assertEqual(a2.points.pos, [(2.0, 0.0), (3.0, 0.0), (3.0, 1.0)])
    self.assertEqual(a2.poly, [0, 1, 2])
    self.assertEqual(a2.holes, [])


# make a closed polygon Subpath from a list of coordinates
def _MakePolySubpath(p):
  subpath = vecfile.Subpath()
  for i in range(len(p)-1):
    subpath.AddSegment(('L', p[i], p[i+1]))
  subpath.closed = True
  return subpath


class TestSubpathToPolyArea(unittest.TestCase):

  def runTest(self):
    subpath = vecfile.Subpath()
    subpath.AddSegment(('L', (0.0, 0.0), (3.0, 0.0)))
    subpath.AddSegment(('L', (3.0, 0.0), (3.0, 5.0)))
    subpath.AddSegment(('B', (3.0, 5.0), (0.0, 5.0), (2.0, 6.0), (1.0, 6.0)))
    subpath.closed = True
    pa = art2polyarea._SubpathToPolyArea(subpath, 1)
    self.assertEqual(pa.points.pos, [(0.0, 0.0), (3.0, 0.0), (3.0, 5.0),
        (1.5, 5.75), (0.0, 5.0)])
    self.assertEqual(pa.poly, [0, 1, 2, 3, 4])
    subpath = vecfile.Subpath()
    subpath.AddSegment(('L', (0.0, 0.0), (1.0, 0.0)))
    pa = art2polyarea._SubpathToPolyArea(subpath, 0)
    self.assertEqual(pa.poly, [])
    subpath = _MakePolySubpath([(0.0, 0.0), (0.000001, 0.0),
        (1.0, 0.0), (2.0, 2.0), (2.0, 2.0004), (3.0, 5.0), (0.0, -0.00003)])
    pa = art2polyarea._SubpathToPolyArea(subpath, 0)
    self.assertEqual(pa.points.pos, [(0.0, 0.0), (1.0, 0.0), (2.0, 2.0), (3.0, 5.0)])
    self.assertEqual(pa.poly, [0, 1, 2, 3])


class TestArtToPolyAreas(unittest.TestCase):

  def runTest(self):
    art = vecfile.Art()
    # path1 - filled with white, so won't appear
    path1 = vecfile.Path()
    path1.AddSubpath(_MakePolySubpath([(1.0, 1.0), (2.0, 1.0), (3.0, 1.0)]))
    path1.filled = True
    path1.fillpaint = vecfile.white_paint
    # path2 - not filled, so won't appear
    path2 = vecfile.Path()
    path2.AddSubpath(_MakePolySubpath([(0.0, 1.0), (3.0, 1.0), (3.0, 1.0)]))
    path2.filled = False
    # path3 - square with triangle hole
    path3 = vecfile.Path()
    path3.AddSubpath(_MakePolySubpath([(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]))
    path3.AddSubpath(_MakePolySubpath([(.2, .2), (.1, .6), (.4, .2)]))
    path3.filled = True
    path3.fillpaint = (1.0, 0.0, 0.0)  # red
    # path 4 - rectangle - covers path3, but shouldn't combine with it
    path4 = vecfile.Path()
    path4.AddSubpath(_MakePolySubpath([(-1.0, -1.0), (5.0, -1.0), (5.0, 2.0), (-1.0, 2.0)]))
    path4.filled = True
    path4.fillpaint = (0.0, 1.0, 0.0)  # green
    art.paths = [path1, path2, path3, path4]
    pas = art2polyarea.ArtToPolyAreas(art, 0, True, False)
    self.assertEqual(len(pas), 2)
    self.assertEqual(pas[0].points.pos,
        [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0), (0.2, 0.2), (0.1, 0.6), (0.4, 0.2)])
    self.assertEqual(pas[0].poly, [0, 1, 2, 3])
    self.assertEqual(pas[0].holes, [[4, 5, 6]])
    self.assertEqual(pas[0].color, (1.0, 0.0, 0.0))
    self.assertEqual(pas[1].points.pos, [(-1.0, -1.0), (5.0, -1.0), (5.0, 2.0), (-1.0, 2.0)])
    self.assertEqual(pas[1].poly, [0, 1, 2, 3])
    self.assertEqual(pas[1].holes, [])
    self.assertEqual(pas[1].color, (0.0, 1.0, 0.0))


if __name__ == "__main__":
  unittest.main()
