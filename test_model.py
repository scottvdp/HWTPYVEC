#!/usr/bin/python3.1

import unittest
import vec
from vec import model
from vec import geom
from vec import offset
from vec import showfaces
import math

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


class TestRotatedPolyAreaToXY(unittest.TestCase):

  def testYZ(self):
    points = geom.Points([(0.,0.,0.),
      (0.,1.,0.), (0.,1.,1.),(0.,0.,1.)])
    pa = geom.PolyArea(points, [0, 1, 2, 3])
    norm = pa.Normal()
    self.assertEqual(norm, (1.0, 0.0, 0.0))
    (pa, transform, newv2oldv) = model._RotatedPolyAreaToXY(pa, norm)
    self.assertEqual(pa.points.pos, [(0.0, 0.0, 0.0),
      (0.0, -1.0, 0.0), (1.0, -1.0, 0.0), (1.0, 0.0, 0.0)])
    for i in range(4):
      newc = pa.points.pos[i]
      oldc = points.pos[newv2oldv[i]]
      self.assertEqual(geom.MulPoint3(newc, transform), oldc)

  def testRevXY(self):
    points = geom.Points([(0.,0.,-1.),
      (1.,0.,-1.), (1.,1.,-1.), (0.,1.,-1.)])
    pa = geom.PolyArea(points, [0, 3, 2, 1])
    norm = pa.Normal()
    self.assertEqual(norm, (0.0, 0.0, -1.0))
    (pa, transform, newv2oldv) = model._RotatedPolyAreaToXY(pa, norm)
    self.assertEqual(pa.points.pos, [(0.0, 0.0, 1.0),
      (-1.0, 0.0, 1.0), (-1.0, -1.0, 1.0), (0.0, -1.0, 1.0)])
    for i in range(4):
      newc = pa.points.pos[i]
      oldc = points.pos[newv2oldv[i]]
      self.assertEqual(geom.MulPoint3(newc, transform), oldc)


def Cube():
  points = geom.Points([
    (-1.,-1.,0.), (1.,-1.,0.), (1.,1.,0.), (-1.,1.,0.),
    (-1.,-1.,1.), (1.,-1.,1.), (1.,1.,1.), (-1.,1.,1.)])
  faces = [
    [0, 3, 2, 1],  # bottom (XY plane)
    [4, 5, 6, 7],  # top (XY plane)
    [0, 1, 5, 4],  # back (XZ plane)
    [3, 7, 6, 2],  # front (XZ plane)
    [1, 2, 6, 5],  # left (YZ plane)
    [0, 4, 7, 3]   # right (YZ plane)
    ]
  m = geom.Model()
  m.points = points
  m.faces = faces
  m.colors = [ (1.,0.,0.) ] * 6
  return m


class TestBevelPolyAreaInModel(unittest.TestCase):

  def testCubeTop(self):
    m = Cube()
    pa = geom.PolyArea(m.points, m.faces[1])
    model.BevelPolyAreaInModel(m, pa, 0.1, math.pi/4., True)
    self.assertEqual(m.points.pos[8:],
      [(-0.9, -0.9, 1.1), (0.9, -0.9, 1.1), (0.9, 0.9, 1.1), (-0.9, 0.9, 1.1)])
    self.assertEqual(m.faces[6:], [[4, 5, 9, 8], [5, 6, 10, 9],
      [6, 7, 11, 10], [7, 4, 8, 11], [8, 9, 10, 11]])

  def testCubeBottom(self):
    m = Cube()
    pa = geom.PolyArea(m.points, m.faces[0])
    model.BevelPolyAreaInModel(m, pa, 0.1, math.pi/4., True)
    print(m.points.pos[8:])
    self.assertEqual(len(m.points.pos), 12)
    self.assertEqual(len(m.faces), 11)


if __name__ == "__main__":
  unittest.main()
