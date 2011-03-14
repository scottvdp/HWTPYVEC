#!/usr/bin/python3.1

import unittest
import vec
from vec import model
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

if __name__ == "__main__":
  unittest.main()
