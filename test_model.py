#!/usr/bin/python3.1

import unittest
import vec
from vec import model
from vec import geom
from vec import offset
from vec import showfaces

SHOW = True  # should we show graphic plots of tested files?

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

if __name__ == "__main__":
  unittest.main()
