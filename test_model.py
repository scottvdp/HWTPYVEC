#!/usr/bin/python3.1

import unittest
import vec
from vec import model
from vec import geom
from vec import offset
from vec import showfaces

SHOW = True  # should we show graphic plots of tested files?

class TestImportAIFile(unittest.TestCase):

  def ReadModel(self, f, options):
    (m, msg) = model.ReadVecFileToModel(f, options)
    self.assertIsNotNone(m)
    self.assertEqual(msg, "")
    if SHOW:
      showfaces.ShowFaces(m.faces, m.points, f)
    return m

  def testO(self):
    self.ReadModel("testfiles/O.ai", model.ImportOptions())

  def testStuff(self):
    self.ReadModel("testfiles/stuff.ai", model.ImportOptions())

  def test43(self):
    opt = model.ImportOptions()
    opt.convert_options.filled_only = False
    opt.convert_options.combine_paths = True
    self.ReadModel("testfiles/4_3.ai", opt)

  def test3dout(self):
    opt = model.ImportOptions()
    opt.convert_options.subdiv_kind = "EVEN"
    self.ReadModel("testfiles/3dout.ai", opt)


class AddOffsetFacesToModel(unittest.TestCase):

  def testTri(self):
    pa = geom.PolyArea(geom.Points([(0.0,0.0),(1.0,0.0),(0.5,0.25)]),
        [0, 1, 2 ])
    o = offset.Offset(pa, 0.0)
    o.Build()
    m = model.Model()
    m.points = pa.points
    model.AddOffsetFacesToModel(m, o, 1.0)
    if SHOW:
      showfaces.ShowFaces(m.faces, m.points, "Tri")

  def testIrreg(self):
    pa = geom.PolyArea(geom.Points([(0.0,0.1),
       (-0.1, -0.2),
       (0.1, -0.25),
       (0.3, 0.05),
       (1.0, 0.0),
       (1.1, 1.0),
       (-0.1, 1.2)]),
       list(range(0,7)))
    o = offset.Offset(pa, 0.0)
    o.Build()
    m = model.Model()
    m.points = pa.points
    model.AddOffsetFacesToModel(m, o, 1.0)
    if SHOW:
      showfaces.ShowFaces(m.faces, m.points, "Irreg")


class TestImportWithExtrude(unittest.TestCase):

  def testExtrude4pt(self):
    opt = model.ImportOptions()
    opt.extrude_depth = 0.5
    opt.convert_options.filled_only = False
    opt.convert_options.smoothness = 0
    (m, msg) = model.ReadVecFileToModel("testfiles/4pt.ai", opt)
    self.assertEqual(msg, "")
    self.assertEqual(len(m.faces), 5)

class TestImportWithBevel(unittest.TestCase):

  def testBevel4pt(self):
    opt = model.ImportOptions()
    opt.bevel_amount = .5
    opt.convert_options.filled_only = False
    opt.convert_options.smoothness = 0
    (m, msg) = model.ReadVecFileToModel("testfiles/4pt.ai", opt)
    self.assertEqual(msg, "")
    self.assertEqual(len(m.faces), 5)
    if SHOW:
      showfaces.ShowFaces(m.faces, m.points, "Bevel 4pt")

  def testBevel4_3(self):
    opt = model.ImportOptions()
    opt.bevel_amount = 0.05
    opt.convert_options.filled_only = False
    opt.convert_options.smoothness = 0
    opt.convert_options.combine_paths = True
    (m, msg) = model.ReadVecFileToModel("testfiles/4_3.ai", opt)
    self.assertEqual(msg, "")
    self.assertEqual(len(m.faces), 13)
    if SHOW:
      showfaces.ShowFaces(m.faces, m.points, "Bevel 4_3")


  def testBevel3dout(self):
    opt = model.ImportOptions()
    opt.bevel_amount = 0.05
    opt.convert_options.filled_only = False
    opt.convert_options.smoothness = 0
    opt.convert_options.combine_paths = True
    (m, msg) = model.ReadVecFileToModel("testfiles/3dout.ai", opt)
    self.assertEqual(msg, "")
    self.assertEqual(len(m.faces), 44)
    if SHOW:
      showfaces.ShowFaces(m.faces, m.points, "Bevel 3dout")


if __name__ == "__main__":
  unittest.main()
