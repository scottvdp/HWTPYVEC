#!/usr/bin/python3.1

import unittest
import vec
from vec import import_vecfile
from vec import model
from vec import geom
from vec import offset
from vec import showfaces

SHOW = True  # should we show graphic plots of tested files?

class TestImportAIFile(unittest.TestCase):

  def ReadModel(self, f, options):
    (m, msg) = import_vecfile.ReadVecFileToModel(f, options)
    self.assertIsNotNone(m)
    self.assertEqual(msg, "")
    if SHOW:
      showfaces.ShowFaces(m.faces, m.points, f)
    return m

  def testO(self):
    self.ReadModel("testfiles/O.ai", import_vecfile.ImportOptions())

  def testStuff(self):
    self.ReadModel("testfiles/stuff.ai", import_vecfile.ImportOptions())

  def test43(self):
    opt = import_vecfile.ImportOptions()
    opt.convert_options.filled_only = False
    opt.convert_options.combine_paths = True
    self.ReadModel("testfiles/4_3.ai", opt)

  def test3dout(self):
    opt = import_vecfile.ImportOptions()
    opt.convert_options.subdiv_kind = "EVEN"
    opt.bevel_amount = 20.0
    self.ReadModel("testfiles/3dout.ai", opt)


class TestImportWithExtrude(unittest.TestCase):

  def testExtrude4pt(self):
    opt = import_vecfile.ImportOptions()
    opt.extrude_depth = 0.5
    opt.convert_options.filled_only = False
    opt.convert_options.smoothness = 0
    (m, msg) = import_vecfile.ReadVecFileToModel("testfiles/4pt.ai", opt)
    self.assertEqual(msg, "")
    self.assertEqual(len(m.faces), 5)

class TestImportWithBevel(unittest.TestCase):

  def testBevel4pt(self):
    opt = import_vecfile.ImportOptions()
    opt.bevel_amount = .5
    opt.convert_options.filled_only = False
    opt.convert_options.smoothness = 0
    (m, msg) = import_vecfile.ReadVecFileToModel("testfiles/4pt.ai", opt)
    self.assertEqual(msg, "")
    self.assertEqual(len(m.faces), 5)
    if SHOW:
      showfaces.ShowFaces(m.faces, m.points, "Bevel 4pt")

  def testBevel4_3(self):
    opt = import_vecfile.ImportOptions()
    opt.bevel_amount = 0.05
    opt.convert_options.filled_only = False
    opt.convert_options.smoothness = 0
    opt.convert_options.combine_paths = True
    (m, msg) = import_vecfile.ReadVecFileToModel("testfiles/4_3.ai", opt)
    self.assertEqual(msg, "")
    self.assertEqual(len(m.faces), 13)
    if SHOW:
      showfaces.ShowFaces(m.faces, m.points, "Bevel 4_3")


  def testBevel3dout(self):
    opt = import_vecfile.ImportOptions()
    opt.bevel_amount = 0.05
    opt.convert_options.filled_only = False
    opt.convert_options.smoothness = 0
    opt.convert_options.combine_paths = True
    (m, msg) = import_vecfile.ReadVecFileToModel("testfiles/3dout.ai", opt)
    self.assertEqual(msg, "")
    self.assertEqual(len(m.faces), 44)
    if SHOW:
      showfaces.ShowFaces(m.faces, m.points, "Bevel 3dout")


if __name__ == "__main__":
  unittest.main()
