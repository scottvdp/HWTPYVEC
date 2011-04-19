#!/usr/bin/python3.1

"""Unit tests for offset module."""

__author__ = "howard.trickey@gmail.com"

import unittest
import math
import tkinter
import vec
from vec import offset
from vec import geom

SHOW = True  # should we show interactive display of built offsets?

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

Vs4 = geom.Points([(0.0,0.1),
       (-0.1, -0.2),
       (0.1, -0.25),
       (0.3, 0.05),
       (1.0, 0.0),
       (1.1, 1.0),
       (-0.1, 1.2)])

F4 = list(range(0,7))

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


class AnimOffset(tkinter.Frame):
  """Tk widget for plotting/animating offset calculation.

  Attributes:
    xspan: float - max difference in x coords in plot
    yspan: float - max difference in y coords in plot
    xorg: float - x coordinate of origin in plot
    yorg: float - y coordinate of origin in plot
    time: float - current time in animation
    c: Canvas - the Tk Canvas used for plotting
    sc: Scale - the Tk Scale used to control time
    offset: Offset - the Offset being animated.
    lines: list of canvas ids for lines
  """

  def __init__(self, offset):
    self.offset = offset
    self.time = 0.0
    self.polygons = []
    self.ovals = []
    self.labels = []
    maxx = -1e6
    maxy = -1e6
    minx = 1e6
    miny = 1e6
    vmap = offset.polyarea.points.pos
    for f in offset.facespokes:
      for s in f:
        p = vmap[s.origin]
        minx = min(minx, p[0])
        maxx = max(maxx, p[0])
        miny = min(miny, p[1])
        maxy = max(maxy, p[1])
    self.xspan = maxx-minx
    self.yspan = maxy-miny
    maxtime = max(self.xspan, self.yspan) / 2.0
    if self.xspan == 0.0:
      self.xspan = 1.0
    if self.yspan == 0.0:
      self.yspan = 1.0
    # add 10% on either end
    self.xorg = minx - 0.1*self.xspan
    self.yorg = miny - 0.1*self.yspan
    self.xspan *= 1.2
    self.yspan *= 1.2
    root = tkinter.Tk()
    tkinter.Frame.__init__(self, root)
    self.sc = tkinter.Scale(root, orient=tkinter.HORIZONTAL, \
        from_=0.0, to=maxtime, resolution=-1, command=self.Slide)
    self.sc.pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
    self.c = tkinter.Canvas(root)
    self.c.pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)
    self.c.bind('<Configure>', self.Reconfigure)

  def Conv(self, p):
    CX = self.c.winfo_width()
    xx = int(CX*(p[0]-self.xorg)/self.xspan)
    CY = self.c.winfo_height()
    yy = int(CY - CY*(p[1]-self.yorg)/self.yspan)
    return (xx, yy)

  def Reconfigure(self, event):
    self.Redraw()

  def Redraw(self):
    for x in self.polygons:
      self.c.delete(x)
    self.polygons = []
    for x in self.ovals:
      self.c.delete(x)
    self.ovals = []
    for x in self.labels:
      self.c.delete(x)
    self.labels = []
    ovalr = int(self.c.winfo_width()/100)
    if ovalr < 1:
      ovalr = 1
    t = self.time
    points = self.offset.polyarea.points
    vmap = points.pos
    used_points = set()
    ostack = [ self.offset ]
    while ostack:
      o = ostack.pop()
      offt = min(self.time - o.timesofar, o.endtime)
      if offt < 0:
        continue
      for f in o.facespokes:
        nf = len(f)
        for i in range(0, nf):
          s = f[i]
          p = self.Conv(vmap[s.origin])
          nexts = f[(i+1) % nf]
          nextp = self.Conv(vmap[nexts.origin])
          q = self.Conv(s.EndPoint(offt, points))
          nextq = self.Conv(nexts.EndPoint(offt, points))
          used_points.add(s.origin)
          used_points.add(nexts.origin)
          used_points.add(s.dest)
          used_points.add(nexts.dest)
          poly = self.c.create_polygon(p[0], p[1], nextp[0], nextp[1],
            nextq[0], nextq[1], q[0], q[1], fill="grey", outline="black")
          self.polygons.append(poly)
      ostack.extend(o.inneroffsets)
    for i in used_points:
      p = self.Conv(vmap[i])
      oval = self.c.create_oval(p[0]-ovalr, p[1]-ovalr,
        p[0]+ovalr, p[1]+ovalr, fill="yellow", outline="black")
      self.ovals.append(oval)
      if ovalr > 6:
        label = self.c.create_text(p[0], p[1]+2, text=str(i))
        self.labels.append(label)

  def Slide(self, newtime):
    self.time = float(newtime)
    self.Redraw()  # could optimize by just adjusting line ends


def ShowOffset(offset):
  anim = AnimOffset(offset)
  tkinter.mainloop()


class TestSpokeVertexEvent(unittest.TestCase):

  def runTest(self):
    pa = geom.PolyArea(Vs1, F1tri)
    o = offset.Offset(pa, 0.0)
    sp = o.facespokes[0][0]
    # spoke goes from (0,0) bisecting (1,0) and (1,.5) lines
    alpha = math.atan(0.5)
    halpha = alpha / 2.0  # angle of spoke
    self.assertAlmostEqual(sp.speed, 1.0/math.sin(halpha))
    self.assertAlmostEqual(sp.dir[0], math.cos(halpha))
    self.assertAlmostEqual(sp.dir[1], math.sin(halpha))
    ev = sp.VertexEvent(o.facespokes[0][1], pa.points)
    # time is height of triangle with base .5 and angle halpha
    # that is also the y value of the intersection point
    self.assertAlmostEqual(ev.time, 0.5*math.tan(halpha))
    self.assertAlmostEqual(ev.event_vertex[1], ev.time)
    self.assertAlmostEqual(ev.event_vertex[0], 0.5)

class TestSpokeNoVertexEvent(unittest.TestCase):

  def runTest(self):
    pts = geom.Points([(0.0,-2.0), (0.5, 0.0), (1.0,0.0), (2.0,1.0), (3.0,0.0)])
    pa = geom.PolyArea(pts, [0,1,2,3,4])
    o = offset.Offset(pa, 0.0)
    sp = o.facespokes[0][1]
    ev = sp.VertexEvent(o.facespokes[0][2], pa.points)
    self.assertEqual(ev, None)

class TestSpokeEdgeEvent(unittest.TestCase):

  def runTest(self):
    pa = geom.PolyArea(Vs1, F1concave)
    o = offset.Offset(pa, 0.0)
    sp = o.facespokes[0][1]
    other = o.facespokes[0][3]
    ev = sp.EdgeEvent(other, o)
    # trig shows t/(.75-h)=sin(alpha) where tan(alpha)=2
    alpha = math.atan(2)
    sinalpha = math.sin(alpha)
    t = 0.75*sinalpha / (1.0 + sinalpha)
    self.assertAlmostEqual(ev.time, t)
    self.assertAlmostEqual(ev.event_vertex[0], 0.5)
    self.assertAlmostEqual(ev.event_vertex[1], 1.0-t)

class TestNextSpokeEvents(unittest.TestCase):

  def runTest(self):
    pa = geom.PolyArea(Vs1, F1tri)
    o = offset.Offset(pa, 0.0)
    sp = o.facespokes[0][0]
    (t, ve, ee) = o.NextSpokeEvents(sp)
    self.assertEqual(len(ve), 1)
    pa = geom.PolyArea(Vs1, F1concave)
    o = offset.Offset(pa, 0.0)
    sp = o.facespokes[0][1]
    (t, ve,ee) = o.NextSpokeEvents(sp)
    self.assertEqual(len(ee), 1)
    self.assertFalse(ee[0].is_vertex_event)
    self.assertEqual(len(ve), 0)

class TestBuild(unittest.TestCase):

  def testTri(self):
    pa = geom.PolyArea(Vs1, F1tri)
    o = offset.Offset(pa, 0.0)
    o.Build()
    self.assertAlmostEqual(o.endtime, 0.11803398875)
    self.assertEqual(len(o.inneroffsets), 0)
    # ShowOffset(o)

  def testRect(self):
    pa = geom.PolyArea(Vs2, [0, 12, 15, 1])
    o = offset.Offset(pa, 0.0)
    o.Build()
    self.assertAlmostEqual(o.endtime, 0.5)
    self.assertEqual(len(o.inneroffsets), 0)
    if SHOW:
      ShowOffset(o)

  def testIrreg(self):
    pa = geom.PolyArea(Vs4, F4)
    o = offset.Offset(pa, 0.0)
    o.Build()
    self.assertAlmostEqual(o.endtime, 0.1155192686)
    self.assertEqual(len(o.inneroffsets), 1)
    if SHOW:
      ShowOffset(o)

  def testConcave(self):
    pa = geom.PolyArea(Vs1, F1concave)
    o = offset.Offset(pa, 0.0)
    o.Build()
    self.assertEqual(len(o.inneroffsets), 2)
    if SHOW:
      ShowOffset(o)

  def testOneHole(self):
    pa = geom.PolyArea(Vs1, F1square)
    pahole = geom.PolyArea(geom.Points([
      (0.3, 0.5), (0.6, 0.65), (0.45, 0.8)]),
      [0, 1, 2])
    pa.AddHole(pahole)
    o = offset.Offset(pa, 0.0)
    o.Build()
    self.assertEqual(len(o.inneroffsets), 1)
    if SHOW:
      ShowOffset(o)

  def testTwoHoles(self):
    pa = geom.PolyArea(Vs1, F1square)
    pahole1 = geom.PolyArea(geom.Points([
      (0.2, 0.5), (0.4, 0.65), (0.45, 0.8)]),
      [0, 1, 2])
    pa.AddHole(pahole1)
    pahole2 = geom.PolyArea(geom.Points([
      (0.5, 0.3), (0.8, 0.35), (0.75, 0.65)]),
      [0, 1, 2])
    pa.AddHole(pahole2)
    o = offset.Offset(pa, 0.0)
    o.Build()
    self.assertEqual(len(o.inneroffsets), 1)
    if SHOW:
      ShowOffset(o)

  def testM(self):
    pa = geom.PolyArea(Vsm, Fsm)
    o = offset.Offset(pa, 0.0)
    o.Build()
    if SHOW:
      ShowOffset(o)
    

class TestInnerPolyAreas(unittest.TestCase):

  def runTest(self):
    pa = geom.PolyArea(Vs1, F1tri)
    o = offset.Offset(pa, 0.0)
    o.Build(0.1)
    pas = o.InnerPolyAreas()
    self.assertEqual(len(pas.polyareas), 1)
    ipa = pas.polyareas[0]
    self.assertEqual(len(ipa.poly), 3)


if __name__ == "__main__":
  unittest.main()
