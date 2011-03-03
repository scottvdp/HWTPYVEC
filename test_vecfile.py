#!/usr/bin/python3.1
# To run just one test in one TestCase, use a command line like:
#    test_vecfile.py TestParseAIFile.testO

import unittest
import vec
from vec import geom
from vec import vecfile
from vec import art2polyarea
from vec import showfaces

SHOW = False  # should we show graphic plots of tested files?


class TestClassifyNofile(unittest.TestCase):

  def runTest(self):
    (ty,ver) = vecfile.ClassifyFile("nonexistentfile")
    self.assertEqual(ty, "error")
    self.assertEqual(ver, "file open error")


class TestClassifyEPS(unittest.TestCase):
  
  def runTest(self):
    (ty,ver) = vecfile.ClassifyFile("testfiles/star.eps")
    self.assertEqual(ty, "eps")
    self.assertEqual(ver, "3.0")
    (ty,ver) = vecfile.ClassifyFile("testfiles/ill/Illustratorfiles/11_04_Sketch&Toons_start 2.ai")
    self.assertEqual(ty, "ai")
    self.assertEqual(ver, "eps")


class TestClassAIpre9(unittest.TestCase):

  def runTest(self):
    (ty, ver) = vecfile.ClassifyFile("testfiles/stuff8.ai")
    self.assertEqual((ty,ver), ("ai", "eps"))
    (ty, ver) = vecfile.ClassifyFile("testfiles/disk.ai")
    self.assertEqual((ty,ver), ("ai", "eps"))


class TestClassAI9(unittest.TestCase):

  def runTest(self):
    (ty, ver) = vecfile.ClassifyFile("testfiles/stuff.ai")
    self.assertEqual((ty,ver), ("ai", "pdf"))


class TestTokenizeAIEPS(unittest.TestCase):

  def runTest(self):
    s = """%!PS-Adobe-3.0
%%EndSetup
% a comment
/xyz 1.0 {ball} -4 (str\(\)) () <AABB>
"""
    toks = vecfile.TokenizeAIEPS(s)
    self.assertEqual(
        toks,
        [(vecfile.TLITNAME, 'xyz'), (vecfile.TNUM, 1.0),
         (vecfile.TNAME, '{'), (vecfile.TNAME, 'ball'), (vecfile.TNAME, '}'),
         (vecfile.TNUM, -4), (vecfile.TSTRING, r'str\(\)'),
         (vecfile.TSTRING, ''), (vecfile.TSTRING, 'AABB')])


class TestParsePS(unittest.TestCase):

  def test_twopaths(self):
    v = lambda x: (vecfile.TNUM, x)
    o = lambda x: (vecfile.TNAME, x)
    toks = [v(0.0), v(1.0), o("m"),
            v(3.0), v(2.0), o("l"), o("S"),
            v(0.0), v(0.0), o("m"),
            v(1.0), v(1.0), o("l"),
            v(1.0), v(5.0), o("l"), o("h"),
            v(0.0), v(0.0), o("m"),
            v(0.5), v(1.0), v(0.5), v(2.0), v(0.0), v(3.0), o("c"),
            v(-0.5), v(2.0), v(-1.0), v(1.0), o("v"),
            v(-1.0), v(-2.0), v(-2.0), v(0.0), o("y"), o("f")
            ]
    art = vecfile.ParsePS(toks)
    path0 = art.paths[0]
    self.assertEqual(len(path0.subpaths), 1)
    self.assertEqual(path0.subpaths[0].segments,
      [("L", (0.0, 1.0), (3.0, 2.0))])
    self.assertEqual(path0.subpaths[0].closed, False)
    self.assertEqual(path0.filled, False)
    self.assertEqual(path0.stroked, True)
    path1 = art.paths[1]
    self.assertEqual(len(path1.subpaths), 2)
    self.assertEqual(path1.subpaths[0].segments,
      [("L", (0.0, 0.0), (1.0, 1.0)), ("L", (1.0, 1.0), (1.0, 5.0)),
      ("L", (1.0, 5.0), (0.0, 0.0))])
    self.assertEqual(path1.subpaths[1].segments,
       [("B", (0.0, 0.0), (0.0,3.0), (0.5,1.0), (0.5,2.0)),
        ("B", (0.0,3.0), (-1.0,1.0), (0.0,3.0), (-0.5,2.0)),
        ("B", (-1.0,1.0), (-2.0,0.0), (-1.0,-2.0), (-2.0,0.0))])
    self.assertEqual(path1.filled, True)
    self.assertEqual(path1.stroked, False)

  def test_aicompound(self):
    v = lambda x: (vecfile.TNUM, x)
    o = lambda x: (vecfile.TNAME, x)
    toks = [o("*u"),
            v(0.0), v(0.0), o("m"),
            v(1.0), v(0.0), o("l"),
            v(1.0), v(1.0), o("l"),
            v(0.0), v(1.0), o("l"),
            v(0.0), v(0.0), o("l"),
            o("f"),
            v(0.1), v(0.1), o("m"),
            v(0.9), v(0.1), o("l"),
            v(0.5), v(0.9), o("l"),
            v(0.1), v(0.1), o("l"),
            o("f"),
            o("*U")
            ]
    art = vecfile.ParsePS(toks, major = "ai", minor = "eps")
    self.assertEqual(len(art.paths), 1)
    path = art.paths[0]
    self.assertEqual(len(path.subpaths), 2)
    self.assertEqual(path.subpaths[0].segments,
      [ ('L', (0.0, 0.0), (1.0, 0.0)), ('L', (1.0, 0.0), (1.0, 1.0)),
      ('L', (1.0, 1.0), (0.0, 1.0)), ('L', (0.0, 1.0), (0.0, 0.0))])
    self.assertEqual(path.subpaths[1].segments,
      [('L', (0.1, 0.1), (0.9, 0.1)), ('L', (0.9, 0.1), (0.5, 0.9)),
      ('L', (0.5, 0.9), (0.1, 0.1))])



def DumpArt(art):
  print("ART")
  for p in art.paths:
    print("path; filled=", p.filled, "fillpaint=", p.fillpaint.color)
    for sp in p.subpaths:
      print(sp.segments)
  

class TestParseAIFile(unittest.TestCase):

  def ParseOneAI(self, f):
    art = vecfile.ParseAIEPSFile("testfiles/" + f)
    if SHOW:
      pareas = art2polyarea.ArtToPolyAreas(art, 0)
      for pa in pareas:
        showfaces.ShowPolyArea(pa, f)

  def test3dout(self):
    self.ParseOneAI("ill/Illustratorfiles/3dout.ai")

  def test4pt(self):
    self.ParseOneAI("4pt.ai")

  def testeg(self):
    self.ParseOneAI("eg.ai")

  def testO(self):
    self.ParseOneAI("O.ai")

  def testRods(self):
    self.ParseOneAI("Rods.ai")


class TestParsePDFFile(unittest.TestCase):

  def runTest(self):
    art = vecfile.ParseVecFile("testfiles/2.pdf")
    if SHOW:
      pareas = art2polyarea.ArtToPolyAreas(art, 0)
      for pa in pareas:
        showfaces.ShowPolyArea(pa, "2.pdf")


if __name__ == "__main__":
  unittest.main()
