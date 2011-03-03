#!/usr/bin/python3.1

"""Unit tests for geom module."""

import unittest
import vec
from vec import geom


class TestPointsQuantize(unittest.TestCase):

  def runTest(self):
    # current DISTTOL is 1e-3
    p = geom.Points.Quantize((1.4341, -10.9066))
    self.assertEqual(p, (1434, -10907))


class TestPointsAddPoint(unittest.TestCase):

  def runTest(self):
    pts = geom.Points()
    self.assertEqual(len(pts.pos), 0)
    v0 = pts.AddPoint((0.5, -1.0))
    self.assertEqual(len(pts.pos), 1)
    self.assertEqual(v0, 0)
    self.assertEqual(pts.pos[0], (0.5, -1.0))
    v1 = pts.AddPoint((0.501, -1.0))
    self.assertEqual(v1, 0)
    v2 = pts.AddPoint((0.502, -1.0))
    self.assertEqual(v2, 1)


class TestPointsAddPoints(unittest.TestCase):

  def runTest(self):
    pts = geom.Points()
    pts.AddPoint((0.0, 0.0))
    pts.AddPoint((1.0, 2.0))
    pts.AddPoint((3.0, 4.0))
    pts2 = geom.Points([(1.0, 2.0), (10.0, 10.0)])
    vmap = pts.AddPoints(pts2)
    self.assertEqual(len(pts.pos), 4)
    self.assertEqual(vmap, [1, 3])
    self.assertEqual(pts.pos[3], (10.0, 10.0))


class TestSignedArea(unittest.TestCase):

  def runTest(self):
    # a parallelogram with base 6, height 3
    pts = geom.Points([(0.0, 0.0), (6.0, 0.0), (7.0, 3.0), (1.0, 3.0)])
    polygon = [0, 1, 2]
    a = geom.SignedArea(polygon, pts)
    self.assertEqual(a, 9.0)
    polygon = [2, 1, 0]
    a = geom.SignedArea(polygon, pts)
    self.assertEqual(a, -9.0)
    polygon = [0, 1, 2, 3]
    a = geom.SignedArea(polygon, pts)
    self.assertEqual(a, 18.0)


class TestPointInside(unittest.TestCase):

  def runTest(self):
    pts = geom.Points([(0.0, 0.0), (5.0, 0.0), (5.0, 4.0), (2.0, 2.0), (0.0, 4.0)])
    polygon = [0, 1, 2, 3, 4]
    ans = geom.PointInside((0.1, 0.1), polygon, pts)
    self.assertEqual(ans, 1)
    ans = geom.PointInside((1.0, 2.0), polygon, pts)
    self.assertEqual(ans, 1)
    ans = geom.PointInside((2.0, 3.0), polygon, pts)
    self.assertEqual(ans, -1)
    ans = geom.PointInside((5.0, 0.0), polygon, pts)
    self.assertEqual(ans, 0)
    ans = geom.PointInside((0.0, 4.0), polygon, pts)
    self.assertEqual(ans, 0)


class TestApproxEqualPoints(unittest.TestCase):

  def runTest(self):
    self.assertTrue(geom.ApproxEqualPoints((1.0, 2.0), (1.0009, 2.0)))
    self.assertFalse(geom.ApproxEqualPoints((1.0, 2.0), (1.002, 2.0)))
    self.assertTrue(geom.ApproxEqualPoints((0.0, 0.1, 0.2), (0.0, 0.1003, 0.1999)))


if __name__ == "__main__":
  unittest.main()
