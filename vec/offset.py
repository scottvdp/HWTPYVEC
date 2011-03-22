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

"""Creating offset polygons inside faces."""

__author__ = "howard.trickey@gmail.com"

import math
from . import triquad
from . import geom
from .triquad import Sub2, Add2, Angle, Ccw, Normalized2, Perp2, Length2, \
                    LinInterp2, TOL
from .geom import Points

AREATOL = 1e-4

class Spoke(object):
  """A Spoke is a line growing from an outer vertex to an inner one.

  A Spoke is contained in an Offset (see below).

  Attributes:
    origin: int - index of origin point in a Points
    dest: int - index of dest point
    is_reflex: bool - True if spoke grows from a reflex angle
    dir: (float, float) - direction vector (normalized)
    speed: float - at time t, other end of spoke is
        origin + t*dir.  Speed is such that the wavefront
        from the face edges moves at speed 1.
    face: int - index of face containing this Spoke, in Offset
    index: int - index of this Spoke in its face
    destface: int - index of face containing Spoke dest
    destindex: int - index of Spoke dest in its face
  """

  def __init__(self, v, prev, next, face, index, points):
    """Set attribute of spoke from points making up initial angle.

    The spoke grows from an angle inside a face along the bisector
    of that angle.  Its speed is 1/sin(.5a), where a is the angle
    formed by (prev, v, next).  That speed means that the perpendicular
    from the end of the spoke to either of the prev->v or v->prev
    edges will grow at speed 1.

    Args:
      v: int - index of point spoke grows from
      prev: int - index of point before v on boundary (in CCW order)
      next: int - index of point after v on boundary (in CCW order)
      points: geom.Points - maps vertex indices to 2d coords
    """

    self.origin = v
    self.dest = v
    self.face = face
    self.index = index
    self.destface = -1
    self.destindex = -1
    vmap = points.pos
    vp = vmap[v]
    prevp = vmap[prev]
    nextp = vmap[next]
    uin = Normalized2(Sub2(vp, prevp))
    uout = Normalized2(Sub2(nextp, vp))
    uavg = Normalized2((0.5*(uin[0]+uout[0]), 0.5*(uin[1]+uout[1])))
    if abs(Length2(uavg)) < TOL:
      # in and out vectors are reverse of each other
      self.dir = uout
      self.is_reflex = False
      self.speed = 1e7
    else:
      # bisector direction is 90 degree CCW rotation of average incoming/outgoing
      self.dir = (-uavg[1], uavg[0])
      self.is_reflex = Ccw(next, v, prev, points)
      ang = Angle(prev, v, next, points)  # in range [0, 180)
      sin_half_ang = math.sin(math.pi*ang / 360.0)
      if abs(sin_half_ang) < TOL:
        self.speed = 1e7
      else:
        self.speed = 1.0 / sin_half_ang

  def __repr__(self):
    """Printing representation of a Spoke."""

    return "@%d+%gt%s <%d,%d>" % (self.origin, \
            self.speed, str(self.dir), \
            self.face, self.index)

  def EndPoint(self, t, points):
    """Return the coordinates of the non-origin point at time t.

    Args:
      t: float - time to find end point
      vmap: list of (float, float) - coordinate map
    Returns:
      (float, float) - coords of spoke's endpoint at time t
    """

    p = points.pos[self.origin]
    d = self.dir
    v = self.speed
    return ((p[0]+v*t*d[0], p[1]+v*t*d[1]))


  def VertexEvent(self, other, points):
    """Intersect self with other spoke, and return the OffsetEvent, if any.

    A vertex event is with one advancing spoke intersects an adjacent
    adavancing spoke, forming a new vertex.

    Args:
      other: Spoke - other spoke to intersect with
      points: Geom.points
    Returns:
      None or OffsetEvent - if there's an intersection in the growing
        directions of the spokes, will return the OffsetEvent for
        the intersection;
        if lines are collinear or parallel, return None
    """

    vmap = points.pos
    a = vmap[self.origin]
    b = Add2(a, self.dir)
    c = vmap[other.origin]
    d = Add2(c, other.dir)
    # find intersection of line ab with line cd
    u = Sub2(b, a)
    v = Sub2(d, c)
    w = Sub2(a, c)
    pp = Perp2(u, v)
    if abs(pp) > TOL:
      # lines or neither parallel nor collinear
      si = Perp2(v, w) / pp
      ti = Perp2(u, w) / pp
      if si >= 0 and ti >= 0:
        p = LinInterp2(a, b, si)
        dist_ab = si*Length2(u)
        dist_cd = ti*Length2(v)
        time_ab = dist_ab / self.speed
        time_cd = dist_cd / other.speed
        time = max(time_ab, time_cd)
        return OffsetEvent(True, time, p, self, other)
    return None

  def EdgeEvent(self, other, offset):
    """Intersect self with advancing edge and return OffsetEvent, if any.

    An edge event is when one advancing spoke intersects an advancing
    edge.  Advancing edges start out as face edges and move perpendicular
    to them, at a rate of 1.  The endpoints of the edge are the advancing
    spokes on either end of the edge (so the edge shrinks or grows as
    it advances). At some time, the edge may shrink to nothing and there
    will be no EdgeEvent after that time.

    We represent an advancing edge by the first spoke (in CCW order
    of face) of the pair of defining spokes.

    At time t, end of this spoke is at
        o + d*s*t
    where o=self.origin, d=self.dir, s= self.speed.
    The advancing edge line has this equation:
        oo + od*os*t + p*a
    where oo, od, os are o, d, s for other spoke, and p is direction
    vector parallel to advancing edge, and a is a real parameter.
    Equating x and y of intersection point:

        o.x + d.x*s*t = oo.x + od.x*os*t + p.x*w
        o.y + d.y*s*t = oo.y + od.y*os*t + p.y*w

    which can be rearranged into the form

        a = bt + cw
        d = et + fw

    and solved for t, w.

    Args:
      other: Spoke - the edge out of this spoke's origin is the advancing
          edge to be checked for intersection
      offset: Offset - the containing Offset
    Returns:
      None or OffsetEvent - with data about the intersection, if any
    """

    vmap = offset.polyarea.points.pos
    o = vmap[self.origin]
    oo = vmap[other.origin]
    otherface = offset.facespokes[other.face]
    othernext = otherface[(other.index+1) % len(otherface)]
    oonext = vmap[othernext.origin]
    p = Normalized2(Sub2(oonext, oo))
    a = o[0] - oo[0]
    d = o[1] - oo[1]
    b = other.dir[0]*other.speed - self.dir[0]*self.speed
    e = other.dir[1]*other.speed - self.dir[1]*self.speed
    c = p[0]
    f = p[1]
    if abs(c) > TOL:
      dem = e - f*b/c
      if abs(dem) > TOL:
        t = (d - f*a/c) / dem
        w = (a - b*t) / c
      else:
        return None
    elif abs(f) > TOL:
      dem = b - c*e/f
      if abs(dem) > TOL:
        t = (a - c*d/f) / dem
        w = (d - e*t) / f
      else:
        return None
    else:
      return None
    if t < 0.0:
      # intersection is in backward direction along self spoke
      return None
    if w < 0.0:
      # intersection is on wrong side of first end of advancing line segment
      return None
    # calculate the equivalent of w for the other end
    aa = o[0] - oonext[0]
    dd = o[1] - oonext[1]
    bb = othernext.dir[0]*othernext.speed - self.dir[0]*self.speed
    ee = othernext.dir[1]*othernext.speed - self.dir[1]*self.speed
    cc = -p[0]
    ff = -p[1]
    if abs(cc) > TOL:
      ww = (aa - bb*t) / cc
    elif abs(ff) > TOL:
      ww = (dd - ee*t) / ff
    else:
      return None
    if ww < 0.0:
      return None
    evertex = (o[0] + self.dir[0]*self.speed*t, \
               o[1] + self.dir[1]*self.speed*t)
    return OffsetEvent(False, t, evertex, self, other)
    

class OffsetEvent(object):
  """An event involving a spoke during offset computation.

  The events kinds are:
    vertex event: the spoke intersects an adjacent spoke and makes a new vertex
    edge event: the spoke hits an advancing edge and splits it

  Attributes:
    is_vertex_event: True if this is a vertex event (else it is edge event)
    time: float - time at which it happens (edges advance at speed 1)
    event_vertex: (float, float) - intersection point of event
    spoke: Spoke - the spoke that this event is for
    other: Spoke - other spoke involved in event; if vertex event, this will
      be an adjacent spoke that intersects; if an edge event, this is the
      spoke whose origin's outgoing edge grows to hit this event's spoke
  """

  def __init__(self, isv, time, evertex, spoke, other):
    """Creates and initializes attributes of an OffsetEvent."""

    self.is_vertex_event = isv
    self.time = time
    self.event_vertex = evertex
    self.spoke = spoke
    self.other = other

  def __repr__(self):
    """Printing representation of an event."""

    if self.is_vertex_event:
      c = "V"
    else:
      c = "E"
    return "%s t=%5f %s %s %s" % (c, self.time, str(self.event_vertex), \
                                  repr(self.spoke), repr(self.other))


class Offset(object):
  """Represents an offset polygonal area, and used to construct one.

  Attributes:
    polyarea: geom.PolyArea - the area we are offsetting from.
        We share the polyarea.points, and add to it as points in
        the offset polygonal area are computed.
    facespokes: list of list of Spoke - each sublist is a closed face
        (oriented CCW); the faces may mutually interfere.
        These lists are spokes for polyarea.poly + polyarea.holes,
        except that the lists of the holes are reversed to make them
        all CCW.
    endtime: float - time when this offset hits its first
        event (relative to beginning of this offset)
    timesofar: float - sum of times taken by all containing Offsets
    inneroffsets: list of Offset - the offsets that take over after this (inside it)
  """

  def __init__(self, polyarea, time):
    """Set up initial state of Offset from a polyarea.

    Args:
      polyarea: geom.PolyArea
      time: float - time so far
    """

    self.polyarea = polyarea
    self.facespokes = []
    self.endtime = 0.0
    self.timesofar = time
    self.inneroffsets = []
    self.InitFaceSpokes(polyarea.poly, True)
    for f in polyarea.holes:
      self.InitFaceSpokes(f, False)

  def __repr__(self):
    ans = ["Offset: endtime=%g" % self.endtime]
    for i, face in enumerate(self.facespokes):
      ans.append(("<%d>" % i) + str([ str(spoke) for spoke in face ]))
    return '\n'.join(ans)

  def InitFaceSpokes(self, face_vertices, isccw):
    """Initialize the offset representation of a face from vertex list.

    If the face has no area or too small an area, don't bother making it.

    Args:
      face_vertices: list of int - point indices for boundary of face
      isccw: bool - True if face goes counterclockwise
    Side effect:
      A new face (list of spokes) may be added to self.facespokes
    """

    n = len(face_vertices)
    if n <= 2:
      return
    points = self.polyarea.points
    area = abs(geom.SignedArea(face_vertices, points))
    if area < AREATOL:
      return
    if isccw:
      previnc = -1
      nextinc = 1
    else:
      previnc = 1
      nextinc = -1
    findex = len(self.facespokes)
    fspokes = [ Spoke(v, face_vertices[(i+previnc) % n], \
        face_vertices[(i+nextinc) % n], findex, i, points) \
        for i, v in enumerate(face_vertices) ]
    self.facespokes.append(fspokes)

  def NextSpokeEvents(self, spoke):
    """Return the OffsetEvents that will next happen for a given spoke.

    It might happen that some events happen essentially simultaneously,
    and also it is convenient to separate Edge and Vertex events, so
    we return two lists.
    But, for vertex events, only look at the event with the next Spoke,
    as the event with the previous spoke will be accounted for when we
    consider that previous spoke.

    Args:
      spoke: Spoke - a spoke in one of the faces of this object
    Returns:
      (float, list of OffsetEvent, list of OffsetEvent) - time of next event,
          next Vertex event list and next Edge event list
    """

    facespokes = self.facespokes[spoke.face]
    n = len(facespokes)
    bestt = 1e100
    bestv = []
    beste = []
    # First find vertex event (only the one with next spoke)
    next_spoke = facespokes[(spoke.index+1) % n]
    ev = spoke.VertexEvent(next_spoke, self.polyarea.points)
    if ev:
      bestv = [ev]
      bestt = ev.time
    # Now find edge events, if this is a reflex vertex
    if spoke.is_reflex:
      prev_spoke = facespokes[(spoke.index-1) % n]
      for f in self.facespokes:
        for other in f:
          if other == spoke or other == prev_spoke:
            continue
          ev = spoke.EdgeEvent(other, self)
          if ev:
            if ev.time < bestt - TOL:
              beste = []
              bestv = []
              bestt = ev.time
            if abs(ev.time - bestt) < TOL:
              beste.append(ev)
              break   # one edge event per spoke is enough
    return (bestt, bestv, beste)

  def Build(self, target = 2e100):
    """Build the complete Offset structure or up until target time.

    Find the next event(s), makes the appropriate inner Offsets
    that are inside this one, and calls Build on those Offsets to continue the
    process until only a single point is left or time reaches target.
    """

    bestt = 1e100
    bestevs = [[], []]
    for f in self.facespokes:
      for s in f:
        (t, ve, ee) = self.NextSpokeEvents(s)
        if t < bestt - TOL:
          bestevs = [[], []]
          bestt = t
        if abs(t-bestt) < TOL:
          bestevs[0].extend(ve)
          bestevs[1].extend(ee)
    if abs(bestt) < TOL:
      # seems to be in a loop, so quit
      return
    self.endtime = bestt
    (ve, ee) = bestevs
    newfaces = []
    if target < self.endtime:
      self.endtime = target
      newfaces = self.MakeNewFaces(self.endtime)
    elif ve and not ee:
      # Only vertex events.
      # Merging of successive vertices in inset face will
      # take care of the vertex events
      newfaces = self.MakeNewFaces(self.endtime)
    else:
      # Edge events too
      newfaces = self.MakeNewFaces(self.endtime)
      for ev in ee:
        self.SplitJoinFaces(newfaces, ev)
    self.CleanFaces(newfaces)
    nexttarget = target - self.endtime
    if len(newfaces) > 0:
      pa = geom.PolyArea(points = self.polyarea.points)
      if len(newfaces) > 1:
        print("Need to implement this")
      pa.poly = newfaces[0]
      pa.color = self.polyarea.color
      self.inneroffsets = [ Offset(pa, self.timesofar+self.endtime) ]
      if nexttarget > TOL:
        for o in self.inneroffsets:
          o.Build(nexttarget)

  def FaceAtSpokeEnds(self, f, t):
    """Return a new face that is at the spoke ends of face f at time t.

    Also merges any adjacent approximately equal vertices into one vertex,
    so returned list may be smaller than len(f).

    Args:
      f: list of Spoke - one of self.faces
      t: float - time
    Returns:
      list of int - indices into self.polyarea.points (which has been extended with new ones)
    """

    newface = []
    points = self.polyarea.points
    for i in range(0, len(f)):
      s = f[i]
      vcoords = s.EndPoint(t, points)
      v = points.AddPoint(vcoords)
      if newface:
        if v != newface[-1] and not (i == len(f)-1 and v == newface[0]):
            newface.append(v)
      else:
        newface.append(v)
      s.dest = v
    return newface

  def MakeNewFaces(self, t):
    """For each face in this offset, make new face extending spokes to time t.

    Args:
      t: double - time
    Returns:
      list of list of int - list of new faces
    """

    ans = []
    for f in self.facespokes:
      newf = self.FaceAtSpokeEnds(f, t)
      if len(newf) > 2:
        ans.append(newf)
    return ans

  def SplitJoinFaces(self, newfaces, ev):
    """Use event ev to split or join faces.
    
    Given ev, an edge event, use the ev spoke to split the
    other spoke's inner edge.
    If the ev's face and destface are the same, this splits the
    face into two; if the faces are different, it joins them into one.
    We have just made faces at the end of the spokes.
    We have to remove the edge going from the other spoke to its
    next spoke, and replace it with two edges, going to and from
    the event spoke's destination.
    General situation:
         __  s  ____
     \     b\ | /a       /
     c\      \|/        /e
      -----------------
    o/        d        \
    /                   \
  
    where s is the event spoke and o is the "other spoke",
    d is o's inner edge, and b is s's inner edge.
    What we are to do is to split d into d1 and d2, with the
    joining point attached where b,s,a join.
    There are a bunch of special cases:
     - one of d1 or d2 might have zero length because end points
       are already coincident or nearly coincident.
     - maybe c==b or e==a

    Args:
      newfaces: list of list of int - the new faces
      ev: OffsetEvent - an edge event
    Side Effects:
      faces in newfaces may be modified or removed, or a new face may
      be added
    """

    findex = ev.spoke.face
    f = newfaces[findex]
    nf = len(f)
    si = ev.spoke.index
    pi = ev.other.index
    newf0 = findex
    newf1 = len(newfaces)
    newface0 = []
    newface1 = []
    # The two new faces put spoke si's dest on edge between
    # pi's dest and qi (edge after pi)'s dest in original face.
    # These are indices in the original face; the current dest face
    # may have fewer elements because of merging successive points
    # TODO: finish this

  def CleanFaces(self, newfaces):
    """Fix up the newfaces"""

    # TODO
    pass

  def InnerPolyAreas(self):
    """Return the interior of the offset (and contained offsets) as PolyAreas.

    Returns:
      geom.PolyAreas
    """

    ans = geom.PolyAreas()
    ans.points = self.polyarea.points
    _AddInnerAreas(self, ans)
    return ans


def _AddInnerAreas(off, polyareas):
  """Add the innermost areas of offset off to polyareas.

  Assume that polyareas is already using the proper shared points.

  Arguments:
    off: Offset
    polyareas: geom.PolyAreas
  Side Effects:
    Any non-zero-area faces in the very inside of off are
    added to polyareas.
  """

  if off.inneroffsets:
    for o in off.inneroffsets:
      _AddInnerAreas(o)
  else:
    newpa = geom.PolyArea(polyareas.points)
    for i, f in enumerate(off.facespokes):
      newface = off.FaceAtSpokeEnds(f, off.endtime)
      area = abs(geom.SignedArea(newface, polyarea.points))
      if area < AREATOL:
        if i == 0:
	  break
	else:
	  continue
      if i == 0:
        newpa.poly = newface
	newpa.color = off.polyarea.color
      else:
        newface.reverse()
        newpa.holes.append(newface)
    if newpa.poly:
      polyareas.polyareas.append(newpa)

        