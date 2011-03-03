#!/usr/bin/python3.1

import unittest
import vec
from vec import model

class TestImportAIFile(unittest.TestCase):

  def ReadModel(self, f):
    (m, msg) = model.ReadVecFileToModel(f, True, 1)
    self.assertIsNotNone(m)
    self.assertEqual(msg, "")
    return m

  def testO(self):
    m = self.ReadModel("testfiles/O.ai")
    m.writeObjFile("testfiles/O.obj")

  def testStuff(self):
    m = self.ReadModel("testfiles/stuff.ai")
    m.writeObjFile("testfiles/stuff.obj")



if __name__ == "__main__":
  unittest.main()
