#!/usr/bin/python3.1

import unittest
import vec
from vec import model
from vec import geom
from vec import offset
from vec import showfaces

SHOW = False  # should we show graphic plots of tested files?

class AddOffsetFacesToModel(unittest.TestCase):

  def testTri(self):
    pa = geom.PolyArea(geom.Points([(0.0,0.0,0.0),(1.0,0.0,0.0),(0.5,0.25,0.0)]),
        [0, 1, 2 ])
    o = offset.Offset(pa, 0.0)
    o.Build()
    m = geom.Model()
    m.points = pa.points
    model.AddOffsetFacesToModel(m, o, 1.0)
    if SHOW:
      showfaces.ShowFaces(m.faces, m.points, "Tri")

  def testIrreg(self):
    pa = geom.PolyArea(geom.Points([(0.0,0.1,0.0),
       (-0.1, -0.2, 0.0),
       (0.1, -0.25, 0.0),
       (0.3, 0.05, 0.0),
       (1.0, 0.0, 0.0),
       (1.1, 1.0, 0.0),
       (-0.1, 1.2, 0.0)]),
       list(range(0,7)))
    o = offset.Offset(pa, 0.0)
    o.Build()
    m = geom.Model()
    m.points = pa.points
    model.AddOffsetFacesToModel(m, o, 1.0)
    if SHOW:
      showfaces.ShowFaces(m.faces, m.points, "Irreg")

def GridPoints(cols, rows):
  points = geom.Points()
  for x in range(cols):
    for y in range(rows):
      points.AddPoint((float(x), float(y), 0.0))
  return points

class TestRegionToPolyAreas(unittest.TestCase):

  def testTwoConnected(self):
    # two squares, side by side sharing a vertical edge
    points = GridPoints(3, 2)
    faces = [ [0, 1, 4, 3], [1, 2, 5, 4] ]
    pas = model.RegionToPolyAreas(faces, points)
    self.assertEqual(len(pas), 1)
    self.assertEqual(pas[0].poly, [0, 1, 2, 5, 4, 3])

  def testtwoDisconnected(self):
    points = GridPoints(4, 2)
    faces = [ [0, 1, 5, 4], [2, 3, 7, 6] ]
    pas = model.RegionToPolyAreas(faces, points)
    self.assertEqual(len(pas), 2)

  def testCross(self):
    points = GridPoints(4, 4)
    faces = [ [1, 2, 6, 5],
      [4, 5, 9, 8], [5, 6, 10, 9], [6, 7, 11, 10],
      [9, 10, 14, 13] ]
    pas = model.RegionToPolyAreas(faces, points)
    self.assertEqual(len(pas), 1)
    self.assertEqual(pas[0].poly,
      [1, 2, 6, 7, 11, 10, 14, 13, 9, 8, 4, 5])

  def testTouch(self):
    points = GridPoints(3, 3)
    faces = [ [0, 1, 4, 3], [4, 5, 8, 7] ]
    pas = model.RegionToPolyAreas(faces, points)
    self.assertEqual(len(pas), 2)

  def testHole(self):
    points = GridPoints(4, 4)
    faces = [ [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6],
      [4, 5, 9, 8], [6, 7, 11, 10],
      [8, 9, 13, 12], [9, 10, 14, 13], [10, 11, 15, 14]]
    pas = model.RegionToPolyAreas(faces, points)
    self.assertEqual(len(pas), 1)
    self.assertEqual(pas[0].poly,
      [0, 1, 2, 3, 7, 11, 15, 14, 13, 12, 8, 4])
    self.assertEqual(len(pas[0].holes), 1)
    self.assertEqual(pas[0].holes[0], [6, 5, 9, 10])


if __name__ == "__main__":
  unittest.main()
