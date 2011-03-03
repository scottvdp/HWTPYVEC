#!/usr/bin/python3.1

"""This module tests the triangulate family of functions provided by triquad.py"""

import unittest
import math
import vec
from vec import geom
from vec import triquad
from vec import showfaces

Show = True    # set True if want to see display of triangulations

# Some test data sets

# Points in pattern:
# 4     3
#
# 
#    2
# 0     1
Vs1 = geom.Points([(0.0,0.0),
	   (1.0,0.0),
	   (0.5,0.25),
	   (1.0,1.0),
	   (0.0,1.0)])

F1tri = [0,1,2]
F1square = [0,1,3,4]
F1concave = [0,2,1,3,4]
F1crosses = [0,1,4,3]

# Points in pattern
# 0                   1
#    2 3        4  5
#         6  7
#    8 9        10 11
# 12      13 14       15
Vs2 = geom.Points([(0.0,1.0), (1.75,1.0),
	   (0.25,0.75), (0.5,0.75), (1.25,0.75), (1.5,0.75),
	   (0.75,0.5), (1.0,0.5),
	   (0.25,0.25), (0.5,0.25), (1.25,0.25), (1.5,0.25),
	   (0.0,0.0), (0.75,0.0), (1.0,0.0), (1.75,0.0)])

F2outer = [0,12,13,6,7,14,15,1]
F2hole1 = [2,3,9,8]
F2hole2 = [5,11,10,4]

# 16 points in circle
Vs3 = geom.Points([(1.00000,0.0),
	   (0.923880,0.382683),
	   (0.707107,0.707107),
	   (0.382683,0.923880),
	   (2.67949e-8,1.000000),
	   (-0.382683,0.923880),
	   (-0.707107,0.707107),
	   (-0.923880,0.382683),
	   (-1.000000,5.35898e-8),
	   (-0.923880,-0.382683),
	   (-0.707107,-0.707107),
	   (-0.382684,-0.923880),
	   (-8.03847e-8,-1.000000),
	   (0.382683,-0.923880),
	   (0.707107,-0.707107),
	   (0.923879,-0.382684)])

F3circle = list(range(0,16))

# Points for lowercase Arial m
Vsm =geom.Points([(0.131836,0.0),	
	  (0.307617,0.0),
	  (0.307617,0.538086),
	  (0.335938,0.754883),
	  (0.427246,0.869141),
	  (0.564453,0.908203),
	  (0.705078,0.849609),
	  (0.748047,0.673828),
	  (0.748047,0.0),		
	  (0.923828,0.0),		
	  (0.923828,0.602539),
	  (0.996094,0.835449),
	  (1.17773,0.908203),		
	  (1.28320,0.879883),		
	  (1.34521,0.805176),
	  (1.36230,0.653320),		
	  (1.36230,0.0),		
	  (1.53711,0.0),
	  (1.53711,0.711914),		
	  (1.45410,0.975098),		
	  (1.21680,1.06055),		
	  (0.896484,0.878906),
	  (0.792480,1.01270),		
	  (0.603516,1.06055),		
	  (0.418945,1.01416),		
	  (0.289063,0.891602),
	  (0.289063,1.03711),		
	  (0.131836,1.03711)])

Fsm = list(range(0,28))


class TestTriangulateFace(unittest.TestCase):

  def testTriangle(self):
    ans = triquad.TriangulateFace(F1tri, Vs1)
    if Show:
      showfaces.ShowFaces(ans, Vs1, "F1tri - tri")
    self.assertEqual(ans, [tuple(F1tri)])

  def testSquare(self):
    ans = triquad.TriangulateFace(F1square, Vs1)
    if Show:
      showfaces.ShowFaces(ans, Vs1, "F1square - tri")
    self.assertEqual(len(ans), 2)

  def testCircle(self):
    ans = triquad.TriangulateFace(F3circle, Vs3)
    if Show:
      showfaces.ShowFaces(ans, Vs3, "F3circle - tri")
    self.assertEqual(len(ans), 14)

  def testM(self):
    ans = triquad.TriangulateFace(Fsm, Vsm)
    if Show:
      showfaces.ShowFaces(ans, Vsm, "Fsm - tri")
    self.assertEqual(len(ans), 26)

  def testHoles(self):
    ans = triquad.TriangulateFaceWithHoles(F2outer, [F2hole1, F2hole2], Vs2)
    if Show:
      showfaces.ShowFaces(ans, Vs2, "F2 - tri")

class TestQuadrangulateFace(unittest.TestCase):

  def testTriangle(self):
    ans = triquad.QuadrangulateFace(F1tri, Vs1)
    if Show:
      showfaces.ShowFaces(ans, Vs1, "F1tri - quad")
    self.assertEqual(ans, [tuple(F1tri)])

  def testSquare(self):
    ans = triquad.QuadrangulateFace(F1square, Vs1)
    if Show:
      showfaces.ShowFaces(ans, Vs1, "F1square - quad")
    self.assertEqual(len(ans), 1)

  def testCircle(self):
    ans = triquad.QuadrangulateFace(F3circle, Vs3)
    if Show:
      showfaces.ShowFaces(ans, Vs3, "F3circle - quad")
    self.assertEqual(len(ans), 9)

  def testM(self):
    ans = triquad.QuadrangulateFace(Fsm, Vsm)
    if Show:
      showfaces.ShowFaces(ans, Vsm, "Fsm - quad")
    self.assertEqual(len(ans), 14)

  def testHoles(self):
    ans = triquad.QuadrangulateFaceWithHoles(F2outer, [F2hole1, F2hole2], Vs2)
    if Show:
      showfaces.ShowFaces(ans, Vs2, "F2 - quad")

class TestAngle(unittest.TestCase):

  def testAngle1(self):
    ans = triquad.Angle(0, 1, 3, Vs1)
    self.assertAlmostEqual(ans, 90.0)

  def testAngle2(self):
    ans = triquad.Angle(3, 1, 0, Vs1)
    self.assertAlmostEqual(ans, 90.0)

  def testAngle3(self):
    ans = triquad.Angle(0, 2, 1, Vs1)
    self.assertAlmostEqual(ans, 126.86989764584402)

class TestSegsintersect(unittest.TestCase):

  def testSegsintersect1(self):
    pts = geom.Points([(0.0,0.0), (1.0,1.0),(1.0,0.0),(0.0,1.0)])
    self.assertTrue(triquad.SegsIntersect(0,1,2,3,pts))
    self.assertTrue(triquad.SegsIntersect(0,1,3,2,pts))

  def testSegsintersect2(self):
    pts = geom.Points([(0.0,0.0), (1.0,1.0),(1.0,0.0),(0.0,1.0)])
    self.assertFalse(triquad.SegsIntersect(0,2,1,3,pts))
    self.assertFalse(triquad.SegsIntersect(2,0,3,1,pts))
    self.assertFalse(triquad.SegsIntersect(0,0,0,1,pts))
    self.assertFalse(triquad.SegsIntersect(0,1,1,1,pts))

  def testSegsintersect3(self):
    pts = geom.Points([(0.0,0.0), (1.0,0.0),(-0.5,-0.5),(0.5,0.5),(0.5,0.1)])
    self.assertFalse(triquad.SegsIntersect(0,1,2,3,pts))
    self.assertTrue(triquad.SegsIntersect(0,1,2,4,pts))

  def testSegsintersect4(self):
    pts = geom.Points([(0.0,0.0),(1.0,0.5),(0.25,0.25),(0.75,-1.0)])
    self.assertTrue(triquad.SegsIntersect(0,1,2,3,pts))

class TestCCW(unittest.TestCase):

  def testCCW1(self):
    pts = geom.Points([(0.0,0.0),(5.0,1.0),(2.0,3.0),(2.0,-3.0),(8.0, 4.0),(10.0,2.0)])
    self.assertTrue(triquad.Ccw(0, 1, 2, pts))
    self.assertTrue(triquad.Ccw(2, 0, 1, pts))
    self.assertTrue(triquad.Ccw(1, 2, 0, pts))
    self.assertFalse(triquad.Ccw(0, 1, 3, pts))
    self.assertTrue(triquad.Ccw(0, 1, 4, pts))
    self.assertFalse(triquad.Ccw(0, 1, 1, pts))
    self.assertFalse(triquad.Ccw(0, 1, 5, pts))

class TestIncircle(unittest.TestCase):

  def testIncircle(self):
    pts = geom.Points([(math.cos(.1),math.sin(.1)),
        (math.cos(1.1),math.sin(1.1)),
        (math.cos(5.0),math.sin(5.0)),
        (1.1*math.cos(2.0),1.1*math.sin(2.0)),
        (.9*math.cos(6.0),.9*math.sin(6.0)),
        (math.cos(6.1),math.sin(6.1))])
    self.assertTrue(triquad.InCircle(0, 1, 2, 4, pts))
    self.assertFalse(triquad.InCircle(0, 1, 2, 3, pts))
    self.assertFalse(triquad.InCircle(0, 1, 2, 5, pts))
    self.assertFalse(triquad.InCircle(0, 2, 1, 4, pts))
    self.assertTrue(triquad.InCircle(0, 2, 1, 3, pts))
    self.assertFalse(triquad.InCircle(0, 2, 1, 5, pts))

  def testIncircle2(self):
    pts = geom.Points([(0.92387900000000001, -0.38268400000000002),
            (0.382683, 0.92388000000000003),
            (2.6794900000000001e-08, 1.0),
            (0.70710700000000004, 0.70710700000000004)])
    self.assertTrue(triquad.InCircle(0, 1, 2, 3, pts))

class TestAnglekind(unittest.TestCase):

  def testAnglekind(self):
    pts = geom.Points([(0.0,0.0), (1.0,0.5), (2.0, 0.0), (1.0,1.0), (0.0,1.0), (-1.0, 1.0)])
    self.assertEqual(triquad._AngleKind(0, 1, 2, pts), triquad.Angreflex)
    self.assertEqual(triquad._AngleKind(1, 2, 3, pts), triquad.Angconvex)
    self.assertEqual(triquad._AngleKind(3, 4, 5, pts), triquad.Angtangential)
    self.assertEqual(triquad._AngleKind(0, 1, 0, pts), triquad.Ang0)

class TestIncone(unittest.TestCase):

  def testIncone(self):
    pts = geom.Points([(0.0,0.0), (1.0,0.0), (1.0,1.0), (2.0,0.0),
            (2.0,2.0), (0.0,2.0)])
    self.assertTrue(triquad._InCone(5, 0, 1, 2, triquad.Angconvex, pts))
    self.assertTrue(triquad._InCone(5, 1, 2, 3, triquad.Angreflex, pts))

class TestBorderedges(unittest.TestCase):

  def testBorderedges(self):
    faces = [[0,1,2],[0,1,3,4]]
    ans = triquad._BorderEdges(faces)
    self.assertEqual(len(ans), 6)
    self.assertTrue((0,1) in ans)
    self.assertTrue((4,0) in ans)

class TestIsreversed(unittest.TestCase):

  def testIsreversed(self):
    pts = geom.Points([(0.0,0.0),(1.0,0.0),(0.2,1.0),(1.2,1.0)])
    tris1 = [[0,1,3],[0,3,2]]
    tris2 = [[0,1,2],[1,3,2]]                                                         
    td1 = triquad._TriDict(tris1)
    td2 = triquad._TriDict(tris2)
    self.assertTrue(triquad._IsReversed((0,3), td1, pts))
    self.assertFalse(triquad._IsReversed((1,2), td2, pts))
    self.assertFalse(triquad._IsReversed((0,1), td1, pts))

class TestReversededges(unittest.TestCase):

  def testReversededges(self):
    pts = geom.Points([(0.0,0.0),(1.0,0.0),(0.2,1.0),(1.2,1.0),(1.5,0.0)])
    tris = [[0,1,3], [0,3,2], [1,4,3]]
    bord = triquad._BorderEdges([[0,1,4,3,2]])
    td = triquad._TriDict(tris)
    ans = triquad._ReveresedEdges(tris, td, bord, pts)
    self.assertEqual(ans, [(0,3)])

class TestIsear(unittest.TestCase):

  def testIsear0(self):
    n = len(Fsm)
    angk = triquad._ClassifyAngles(Fsm, n, Vsm)
    self.assertTrue(triquad._IsEar(Fsm, 0, n, angk, Vsm, 0))
    f = Fsm[1:]
    angk = triquad._ClassifyAngles(f, n-1, Vsm)
    self.assertFalse(triquad._IsEar(f, 26, n-1, angk, Vsm, 0))
    
class TestCDT(unittest.TestCase):

  def testCDT1(self):
    pts = geom.Points([(0.0,0.0),(1.0,0.0),(0.2,1.0),(1.2,1.0),(1.5,0.0)])
    tris = [(0,1,3), (0,3,2), (1,4,3)]
    bord = triquad._BorderEdges([[0,1,4,3,2]])
    ans = triquad._CDT(tris, bord, pts)
    self.assertEqual(ans, [(1, 4, 3), (2, 0, 1), (2, 1, 3)])

class TestSortface(unittest.TestCase):

  def testSortface(self):
    ans = triquad._SortFace(F3circle, Vs3)
    self.assertEqual(len(ans), len(F3circle))
    self.assertEqual(ans[0], 8)

class TestIsdiag(unittest.TestCase):

  def testIsdiag(self):
    self.assertTrue(triquad._IsDiag(1, 12, 8, F2outer, Vs2))
    self.assertFalse(triquad._IsDiag(1, 12, 11, F2outer, Vs2))

class TestFinddiag(unittest.TestCase):

  def testFinddiag(self):
    self.assertEqual(1, triquad._FindDiag(F2outer, 8, Vs2))

class TestLeftmostface(unittest.TestCase):

  def testLeftmostface(self):
    h1 = triquad._SortFace(F2hole1,Vs2)
    h2 = triquad._SortFace(F2hole2,Vs2)
    holes = [h2, h1]
    self.assertEqual((h1,1), triquad._LeftMostFace(holes, Vs2))

class TestJoinislands(unittest.TestCase):

  def testJoinislands(self):
    holes = [ triquad._SortFace(F2hole1,Vs2), triquad._SortFace(F2hole2,Vs2)]
    ans = triquad._JoinIslands(F2outer, holes, Vs2)
    self.assertEqual(ans, [0, 12, 8, 2, 3, 9, 8, 12, 13, 6,
                           7, 10, 4, 5, 11, 10, 7, 14, 15, 1])

class TestMaxMatch(unittest.TestCase):

  def testMaxMatch(self):
    er = [(1.0, (1, 2), (1, 2, 3), (2, 1, 4)),
          (2.0, (2, 4), (3, 5, 4), (2, 1, 4))]
    ans = triquad._MaxMatch(er)
    self.assertEqual(ans, [(2.0, (2, 4), (3, 5, 4), (2, 1, 4))])
    # Next test has vertices 1-7 in CW ring with an inner ring
    # of vertices 8-11.  The face graph is a circle with a stem.
    er = [(2.0, (2, 7), (1, 2, 7), (2, 7, 6)),
          (1.5, (2, 6), (2, 7, 6), (2, 6, 11)),
          (0.0, (6, 11), (2, 6, 11), (5, 11, 6)),
          (2.0, (5, 11), (5, 11, 6), (5, 10, 11)),
          (0.0, (5, 10), (5, 10, 11), (4, 10, 5)),
          (1.5, (4, 10), (4, 10, 5), (4, 9, 10)),
          (1.0, (4, 9), (4, 9, 10), (3, 9, 4)),
          (1.5, (3, 9), (3, 9, 4), (2, 8, 3)),
          (0.0, (2, 8), (2, 8, 3), (2, 11, 8)),
          (2.0, (2, 11), (2, 11, 8), (2, 6, 11))]
    ans = triquad._MaxMatch(er)
    # use set comparison because random number generator may
    # end up putting answer edges in different orders
    self.assertEqual(set(ans),
                     set([(2.0, (2, 7), (1, 2, 7), (2, 7, 6)),
                      (1.5, (4, 10), (4, 10, 5), (4, 9, 10)),
                      (1.5, (3, 9), (3, 9, 4), (2, 8, 3)),
                      (2.0, (2, 11), (2, 11, 8), (2, 6, 11)),
                      (2.0, (5, 11), (5, 11, 6), (5, 10, 11))]))

if __name__=='__main__':
  unittest.main()
