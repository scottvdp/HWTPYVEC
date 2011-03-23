# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

"""Geometry classes and operations.
representation (Art), and functions for cleaning them up.
"""

__author__ = "howard.trickey@gmail.com"

import math

# distances less than about DISTTOL will be considered
# essentially zero
DISTTOL = 1e-3
INVDISTTOL = 1e3


class Points(object):
  """Container of points without duplication, each mapped to an int.

  Points are either have dimension at least 2, maybe more.

  Implementation:
  In order to efficiently find duplicates, we quantize the points
  to triples of ints and map from quantized triples to vertex
  index.  When searching to see if a point already exists, we
  check each of the 9 buckets for (x, y) with x and y within
  1 of the given quantization.
  For 3d coordinates, we require exact match on
  quantized z, since we control z ourselves in  all our
  applications of this library.

  Attributes:
    pos: list of tuple of float - coordinates indexed by
        vertex number
    invmap: dict of (int, int, int) to int - quantized coordinates
        to vertex number map
  """

  def __init__(self, initlist = []):
    self.pos = []
    self.invmap = dict()
    for p in initlist:
      self.AddPoint(p)

  @staticmethod
  def Quantize(p):
    """Quantize the float tuple into an int tuple.

    Args:
      p: tuple of float
    Returns:
      tuple of int - scaled by INVDISTTOL and rounded p
    """

    return tuple([int(round(v*INVDISTTOL)) for v in p])

  def AddPoint(self, p):
    """Add point p to the Points set and return vertex number.

    If there is an existing point within DISTTOL in all dimensions,
    don't add a new one but instead return existing index.

    Args:
      p: tuple of float - coordinates (2-tuple or 3-tuple)
    Returns:
      int - the vertex number of added (or existing) point
    """

    qp = Points.Quantize(p)
    qx = qp[0]
    qy = qp[1]
    for i in range(-1, 2):
      for j in range(-1, 2):
        tryqp = (qx+i, qy+j) + qp[2:]
        if tryqp in self.invmap:
          return self.invmap[tryqp]
    self.invmap[qp] = len(self.pos)
    self.pos.append(p)
    return len(self.pos)-1

  def AddPoints(self, points):
    """Add another set of points to this set.

    We need to return a mapping from indices
    in the argument points space into indices
    in this point space.

    Args:
      points: Points - to union into this set
    Returns:
      list of int: maps added indices to new ones
    """

    vmap = [ 0 ] * len(points.pos)
    for i in range(len(points.pos)):
      vmap[i] = self.AddPoint(points.pos[i])
    return vmap

  def AddZCoord(self, z):
    """Change this in place to have a z coordinate, with value z.

    Assumes the coordinates are currently 2d.

    Args:
      z: the value of the z coordinate to add
    Side Effect:
      self now has a z-coordinate added
    """

    assert(len(self.pos) == 0 or len(self.pos[0]) == 2)
    tmp = Points()
    for (x,y) in self.pos:
      tmp.AddPoint((x, y, z))
    self.pos = tmp.pos
    self.invmap = tmp.invmap

  def ChangeZCoord(self, i, z):
    """Change the z-coordinate of point with index i.

    Assumes the coordinates are currently 3d.

    Args:
      i: int - index of a point
      z: float - value to change z-coord to
    """

    (x, y, _) = self.pos[i]
    self.pos[i] = (x, y, z)


class PolyArea(object):
  """Contains a Polygonal Area (polygon with possible holes).

  A polygon is a list of vertex ids, each an index given by
  a Points object. The list represents a CCW-oriented
  outer boundary (implicitly closed).
  If there are holes, they are lists of CW-oriented vertices
  that should be contained in the outer boundary.
  (So the left face of both the poly and the holes is
  the filled part.)

  Attributes:
    points: Points
    poly: list of vertex ids
    holes: list of lists of vertex ids (each a hole in poly)
    color: (float, float, float)- rgb color used to fill
  """

  def __init__(self, points = None, poly = None, holes = None):
    self.points = points if points else Points()
    self.poly = poly if poly else []
    self.holes = holes if holes else []
    self.color = (0.0, 0.0, 0.0)

  def AddHole(self, holepa):
    """Add a PolyArea's poly as a hole of self.

    Need to reverse the contour and
    adjust the the point indexes and self.points.

    Args:
      holepa: PolyArea
    """

    vmap = self.points.AddPoints(holepa.points)
    holepoly = [ vmap[i] for i in holepa.poly ]
    holepoly.reverse()
    self.holes.append(holepoly)


class PolyAreas(object):
  """Contains a list of PolyAreas and a shared Points.

  Attributes:
    polyareas: list of PolyArea
    points: Points
  """

  def __init__(self):
    self.polyareas = []
    self.points = Points()

  def scale_and_center(self, scaled_side_target):
    """Adjust the coordinates of the polyareas so that
    it is centered at the origin and has its longest
    dimension scaled to be scaled_side_target."""

    if len(self.points.pos) == 0:
      return
    (minv, maxv) = self.bounds()
    maxside = max([ maxv[i]-minv[i] for i in range(2) ])
    if maxside > 0.0:
      scale = scaled_side_target / maxside
    else:
      scale = 1.0
    translate = [ -0.5*(maxv[i]+minv[i]) for i in range(2) ]
    dim = len(self.points.pos[0])
    if dim == 3:
      translate.append([0.0])
    for v in range(len(self.points.pos)):
      self.points.pos[v] = tuple([ scale*(self.points.pos[v][i] + translate[i]) for i in range(dim) ])

  def bounds(self):
    """Find bounding box of polyareas in xy. 

    Returns:
      ([minx,miny],[maxx,maxy]) - all floats
    """

    huge = 1e100
    minv = [huge, huge]
    maxv = [-huge, -huge]
    for pa in self.polyareas:
      for face in [ pa.poly ] + pa.holes:
        for v in face:
          vcoords = self.points.pos[v]
          for i in range(2):
            if vcoords[i] < minv[i]:
              minv[i] = vcoords[i]
            if vcoords[i] > maxv[i]:
              maxv[i] = vcoords[i]
    if minv[0] == huge:
      minv = [0.0, 0.0]
    if maxv[0] == huge:
      maxv = [0.0, 0.0]
    return (minv, maxv)



def ApproxEqualPoints(p, q):
  """Return True if p and q are approximately the same points.

  Args:
    p: n-tuple of float
    q: n-tuple of float
  Returns:
    bool - True if the 1-norm <= DISTTOL
  """

  for i in range(len(p)):
    if abs(p[i] - q[i]) > DISTTOL:
      return False
    return True


def PointInside(v, a, points):
  """Return 1, 0, or -1 as v is inside, on, or outside polygon.

  Cf. Eric Haines ptinpoly in Graphics Gems IV.

  Args:
    v : (float, float) - coordinates of a point
    a : list of vertex indices defining polygon (assumed CCW)
    points: Points - to get coordinates for polygon
  Returns:
    1, 0, -1: as v is inside, on, or outside polygon a
  """

  (xv, yv) = v
  (x0, y0) = points.pos[a[-1]]
  if x0 == xv and y0 == yv:
    return 0
  yflag0 = y0 > yv
  inside = False
  n = len(a)
  for i in range(0, n):
    (x1, y1) = points.pos[a[i]]
    if x1 == xv and y1 == yv:
      return 0
    yflag1 = y1 > yv
    if yflag0 != yflag1:
      xflag0 = x0 > xv
      xflag1 = x1 > xv
      if xflag0 == xflag1:
        if xflag0:
          inside = not inside
      else:
        z = x1 - (y1-yv)*(x0-x1)/(y0-y1)
        if z >= xv:
          inside = not inside
    x0 = x1
    y0 = y1
    yflag0 = yflag1
  if inside:
    return 1
  else:
    return -1


def SignedArea(polygon, points):
  """Return the area of the polgon, positive if CCW, negative if CW.

  Args:
    polygon: list of vertex indices
    points: Points
  Returns:
    float - area of polygon, positive if it was CCW, else negative
  """

  a = 0.0
  n = len(polygon)
  for i in range(0, n):
    u = points.pos[polygon[i]]
    v = points.pos[polygon[(i+1) % n]]
    a += u[0]*v[1] - u[1]*v[0]
  return 0.5*a


def VecSub(a, b):
  """Return vector a-b.

  Args:
    a: n-tuple of floats
    b: n-tuple of floats
  Returns:
    n-tuple of floats - pairwise subtraction a-b
  """

  n = len(a)
  assert(n == len(b))
  return tuple([ a[i]-b[i] for i in range(n)])


def VecLen(a):
  """Return the Euclidean lenght of the argument vector.

  Args:
    a: n-tuple of floats
  Returns:
    float: the 2-norm of a
  """

  s = 0.0
  for v in a:
    s += v*v
  return math.sqrt(s)


  