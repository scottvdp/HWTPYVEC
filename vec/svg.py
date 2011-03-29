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

"""Reading SVG file format.
"""

__author__ = "howard.trickey@gmail.com"

import re
import xml.dom.minidom
from . import geom
from . import vecfile


def ParseSVGFile(filename):
  """Parse an SVG file name and return an Art object for it.

  Args:
    filename: string - name of file to read and parse
  Returns:
    geom.Art
  """

  dom = xml.dom.minidom.parse(filename)
  return _SVGDomToArt(dom)


def ParseSVGString(s):
  """Parse an SVG string and return an Art object for it.

  Args:
    s: string - contains svg
  Returns:
    geom.Art
  """

  dom = xml.dom.minidom.parseString(s)
  return _SVGDomToArg(dom)


class _SState(object):
  """Holds state that affects the conversion.
  """

  def __init__(self):
    self.ctm = geom.TransformMatrix()
    self.fill = None
    self.stroke = None
    self.dpi = 100


def _SVGDomToArt(dom):
  """Convert an svg file in dom form into an Art object.

  Args:
    dom: xml.dom.minidom.Document
  Returns:
    geom.Art
  """

  art = geom.Art()
  svgs = dom.getElementsByTagName('svg')
  if len(svgs) == 0:
    return art
  gs = _SState()
  # default coordinate system for svg has y downwards
  # so start transform matrix to reverse that
  gs.ctm.d = -1.0
  _ProcessChildren(svgs[0], art, gs)
  return art


def _ProcessChildren(nodes, art, gs):
  """Process a list of SVG nodes, updating art.

  Args:
    nodes: list of xml.dom.Node
    art: geom.Art
    gs: _SState
  Side effects:
    Maybe adds paths to art.
  """

  for node in nodes.childNodes:
    _ProcessNode(node, art, gs)


def _ProcessNode(node, art, gs):
  """Process an SVG node, updating art.

  Args:
    node: xml.dom.Node
    art: geom.Art
    gs: _SState
  Side effects:
    Maybe adds paths to art.
  """

  if node.nodeType != node.ELEMENT_NODE:
    return
  tag = node.tagName
  if tag == 'g':
    _ProcessChildren(node, art, gs)
  elif tag == 'defs':
    pass  # TODO
  elif tag == 'path':
    _ProcessPath(node, art, gs)
  elif tag == 'polygon':
    _ProcessPolygon(node, art, gs)
  elif tag == 'rect':
    pass  # TODO
  elif tag == 'ellipse':
    pass  # TODO


def _ProcessPolygon(node, art, gs):
  """Process a 'polygon' SVG node, updating art.

  Args:
    node: xml.dom.Node - a 'polygon' node
    arg: geom.Art
    gs: _SState
  Side effects:
    Adds path for polygon to art
  """

  if node.hasAttribute('points'):
    coords = _ParseCoordPairList(node.getAttribute('points'))
    n = len(coords)
    if n > 0:
      c = [ gs.ctm.Apply(coords[i]) for i in range(n) ]
      sp = geom.Subpath()
      sp.segments = [ ('L', c[i], c[i % n]) for i in range(n) ]
      sp.closed = True
      path = geom.Path()
      _SetPathAttributes(path, node, gs)
      path.subpaths = [ sp ]
      art.paths.append(path)


def _ProcessPath(node, art, gs):
  """Process a 'polygon' SVG node, updating art.

  Args:
    node: xml.dom.Node - a 'polygon' node
    arg: geom.Art
    gs: _SState
  Side effects:
    Adds path for polygon to art
  """

  if not node.hasAttribute('d'):
    return
  s = node.getAttribute('d')
  i = 0
  n = len(s)
  path = geom.Path()
  _SetPathAttributes(path, node, gs)
  initpt = (0.0, 0.0)
  subpath = None
  while i < len(s):
    (i, subpath, initpt) = _ParseSubpath(s, i, initpt, gs)
    if subpath:
      if not subpath.Empty():
        path.AddSubpath(subpath)
    else:
      break
  if path.subpaths:
    art.paths.append(path)


def _ParseSubpath(s, i, initpt, gs):
  """Parse a moveto-drawto-command-group starting at s[i] and return Subpath.

  Args:
    s: string - should be the 'd' attribute of a 'path' element
    i: int - index in s to start parsing
    initpt: (float, float) - coordinates of initial point
    gs: _SState - used to transform coordinates
  Returns:
    (int, geom.Subpath, (float, float)) - (index after subpath and subsequent whitespace,
        the Subpath itself or Non if there was an error, final point)
  """

  subpath = geom.Subpath()
  i = _SkipWS(s, i)
  n = len(s)
  if i >= n:
    return (i, None, initpt)
  if s[i] == 'M':
    move_cmd = 'M'
  elif s[i] == 'm':
    move_cmd = 'm'
  else:
    return (i, None, initpt)
  (i, cur) = _ParseCoordPair(s, _SkipWS(s, i+1))
  if not cur:
    return (i, None, initpt)
  prev_cmd = 'L'  # implicit cmd if coords follow directly
  if move_cmd == 'm':
    cur = geom.VecAdd(initpt, cur)
    prev_cmd = 'l'
  while True:
    implicit_cmd = False
    if i < n:
      cmd = s[i]
      if _PeekCoord(s, i):
        cmd = prev_cmd
        implicit_cmd = True
    else:
      cmd = None
    if cmd == 'z' or cmd == 'Z' or cmd == None:
      if cmd:
        i = _SkipWS(s, i+1)
        subpath.closed = True
      return (i, subpath, cur)
    elif cmd == 'l' or cmd == 'L':
      if not implicit_cmd:
        i = _SkipWS(s, i+1)
      (i, p1) = _ParseCoordPair(s, i)
      if not p1:
          return  (i, None, cur)
      if cmd == 'l':
        p1 = geom.VecAdd(cur, p1)
      subpath.AddSegment(_LineSeg(cur, p1, gs))
      cur = p1
    elif cmd == 'c' or cmd == 'C':
      if not implicit_cmd:
        i = _SkipWS(s, i+1)
      (i, p1, p2, p3) = _ParseThreeCoordPairs(s, i)
      if not p1:
        return (i, None, cur)
      if cmd == 'c':
        p1 = geom.VecAdd(cur, p1)
        p2 = geom.VecAdd(cur, p2)
        p3 = geom.VecAdd(cur, p3)
      subpath.AddSegment(_Bezier3Seg(cur, p3, p1, p2, gs))
      cur = p3
    elif cmd == 'a' or cmd == 'A':
      if not implicit_cmd:
        i = _SkipWS(s, i+1)
      (i, p1, rad, rot, la, ccw) = _ParseArc(s, i)
      if not p1:
        return (i, None, cur)
      if cmd == 'a':
        p1 = geom.VecAdd(cur, p1)
      subpath.AddSegment(_ArcSeg(cur, p1, rad, rot, la, ccw, gs))
      cur = p1
    else:
      break
    i = _SkipCommaSpace(s, i)
    prev_cmd = cmd
  return (i, None, cur)


def _LineSeg(p1, p2, gs):
  """Return an 'L' segment, transforming coordinates.

  Args:
    p1: (float, float) - start point
    p2: (float, float) - end point
    gs: _SState - used to transform coordinates
  Returns:
    tuple - an 'L' type geom.Subpath segment
  """

  return ('L', gs.ctm.Apply(p1), gs.ctm.Apply(p2))


def _Bezier3Seg(p1, p2, c1, c2, gs):
  """Return a 'B' segment, transforming coordinates.

  Args:
    p1: (float, float) - start point
    p2: (float, float) - end point
    c1: (float, float) - first control point
    c2: (float, float) - second control point
    gs: _SState - used to transform coordinates
  Returns:
    tuple - an 'L' type geom.Subpath segment
  """

  return ('B', gs.ctm.Apply(p1), gs.ctm.Apply(p2),
      gs.ctm.Apply(c1), gs.ctm.Apply(c2))


def _ArcSeg(p1, p2, rad, rot, la, ccw, gs):
  """Return an 'A' segment, with attempt to transform.

  Our A segments don't allow modeling the effect of
  arbitrary transforms, but we can handle translation
  and scaling.

  Args:
    p1: (float, float) - start point
    p2: (float, float) - end point
    rad: (float, float) - (x radius, y radius)
    rot: float - x axis rotation, in degrees
    la: bool - large arc if True
    ccw: bool - counter-clockwise if True
    gs: _SState - used to transform
  Returns:
    tuple - an 'A' type geom.Subpath segment
  """

  tp1 = gs.ctm.Apply(p1)
  tp2 = gs.ctm.Apply(p2)
  rx = rad[0] * gs.ctm.a
  ry = rad[1] * gs.ctm.d
  # if one of axes is mirrored, invert the ccw flag
  if rx * ry < 0.0:
    ccw = not ccw
  trad = (abs(rx), abs(ry))
  # TODO: abs(gs.ctm.a) != abs(ts.ctm.d), adjust xrot
  return ('A', tp1, tp2, trad, rot, la, ccw)


def _SetPathAttributes(path, node, gs):
  """Set the attributes related to filling/stroking in path.

  Use attribute settings in node, if there, else those in the
  current graphics state, gs.

  Arguments:
    path: geom.Path
    node: xml.dom.Node
    gs: _SState
  Side effects:
    May set filled, fillevenodd, stroked, fillpaint, strokepaint in path.
  """

  if node.hasAttribute('fill'):
    path.fillpaint = _ParsePaint(node.getAttribute('fill'))
    if path.fillpaint:
      path.filled = True
  elif gs.fill:
    path.filled = True
    path.fillpaint = gs.fill
  if node.hasAttribute('stroke'):
    path.strokepaint = _ParsePaint(node.getAttribute('stroke'))
    if path.strokepaint:
      path.stroked = True
  elif gs.stroke:
    path.stroked = True
    path.strokepaint = gs.stroke
  if node.hasAttribute('fill-rule'):
    path.fillevenodd = node.getAttribute('fill-rule') == 'evenodd'


# Some useful regular expressions
_re_float = re.compile(r"(\+|-)?(([0-9]+\.[0-9]*)|(\.[0-9]+)|([0-9]+))")
_re_int = re.compile(r"(\+|-)?[0-9]+")
_re_wsopt = re.compile(r"\s*")
_re_wscommaopt = re.compile(r"(\s*,\s*)|(\s*)")


def _ParsePaint(s):
  """Parse an SVG paint definition and return our version of Paint.

  If fail to parse, or the color is 'none', return None.

  Args:
    s: string - should contain an SVG paint spec
  Returns:
    geom.Paint or None
  """

  if len(s) == 0 or s == 'none':
    return None
  if s[0] == '#':
    if len(s) == 7:
      # 6 hex digits
      return geom.Paint( \
        int(s[1:3], 16) / 255.0,
        int(s[3:5], 16) / 255.0,
        int(s[5:7], 16) / 255.0)
    elif len(s) == 4:
      # 3 hex digits
      return geom.Paint( \
        int(s[1], 16)*17 / 255.0,
	int(s[2], 16)*17 / 255.0,
	int(s[3], 16)*17 / 255.0)
  else:
    if s in geom.ColorDict:
      return geom.ColorDict[s]
  return None


def _ParseCoord(s, i):
  """Parse a coordinate (floating point number).

  Args:
    s: string
    i: int - where to start parsing
  Returns:
    (int, float or None) - int is index after the coordinate
      and subsequent white space
  """

  m = _re_float.match(s, i)
  if m:
    return (_SkipWS(s, m.end()), float(m.group()))
  else:
    return (i, None)


def _PeekCoord(s, i):
  """Return True if s[i] starts a coordinate.

  Args:
    s: string
    i: int - place in s to start looking
  Returns:
    bool - True if s[i] starts a coordinate, perhaps after comma / space
  """

  i = _SkipCommaSpace(s, i)
  m = _re_float.match(s, i)
  return True if m else False


def _ParseCoordPair(s, i):
  """Parse pair of coordinates, with optional comma between.

  Args:
    s: string
    i: int - where to start parsing
  Returns:
    (int, (float, float) or None) - int is index after the coordinate
      and subsequent white space
  """

  (j, x) = _ParseCoord(s, i)
  if x is not None:
    j = _SkipCommaSpace(s, j)
    (j, y) = _ParseCoord(s, j)
    if y is not None:
      return (_SkipWS(s, j), (x, y))
  return (i, None)


def _ParseTwoCoordPairs(s, i):
  """Parse two coordinate pairs, optionally separated by commas.

  Args:
    s: string
    i: int - where to start parsing
  Returns:
    (int, (float, float) or None, (float, float) or None) - int is index after the coordinate
      and subsequent white space
  """

  (j, pair1) = _ParseCoordPair(s, i)
  if pair1:
    j = _SkipCommaSpace(s, j)
    (j, pair2) = _ParseCoordPair(s, j)
    if pair2:
      return (j, pair1, pair2)
  return (i, None, None)


def _ParseThreeCoordPairs(s, i):
  """Parse three coordinate pairs, optionally separated by commas.

  Args:
    s: string
    i: int - where to start parsing
  Returns:
    (int, (float, float) or None, (float, float) or None, (float, float) or None) -
      int is index after the coordinateand subsequent white space
  """

  (j, pair1) = _ParseCoordPair(s, i)
  if pair1:
    j = _SkipCommaSpace(s, j)
    (j, pair2) = _ParseCoordPair(s, j)
    if pair2:
      j = _SkipCommaSpace(s, j)
      (j, pair3) = _ParseCoordPair(s, j)
      if pair3:
        return (j, pair1, pair2, pair3)
  return (i, None, None, None)


def _ParseCoordPairList(s):
  """Parse a list of coordinate pairs.

  The numbers should be separated by whitespace
  or a comma with optional whitespace around it.

  Args:
    s: string - should contain coordinate pairs
  Returns:
    list of (float, float)
  """

  ans = []
  i = _SkipWS(s, 0)
  while i < len(s):
    (i, pair) = _ParseCoordPair(s, i)
    if not pair:
      break
    ans.append(pair)
  return ans


def _ParseArc(s, i):
  """Parse an elliptical arc specification.

  Args:
    s: string
    i: int - where to start parsing
  Returns:
    (int, (float, float) or None, (float, float), float, bool, bool) -
      int is index after spec and subsequent white space,
      first (float, float) is end point of arc
      second (float, float) is (x-radius, y-radius)
      float is x-axis rotation, in degrees
      first bool is True if larger arc is to be used
      second bool is True if arc follows ccw direction
  """

  (j, rad) = _ParseCoordPair(s, i)
  if rad:
    j = _SkipCommaSpace(s, j)
    (j, rot) = _ParseCoord(s, j)
    if rot is not None:
      j = _SkipCommaSpace(s, j)
      (j, f) = _ParseCoord(s, j)  # OK, should really just look for 0 or 1
      if f is not None:
        laf = (f != 0.0)
        j = _SkipCommaSpace(s, j)
        (j, f) = _ParseCoord(s, j)
        if f is not None:
          ccw = (f != 0.0)
          j = _SkipCommaSpace(s, j)
          (j, pt) = _ParseCoordPair(s, j)
          if pt:
            return (j, pt, rad, rot, laf, ccw)
  return (i, None, None, None, None, None)


def _SkipWS(s, i):
  """Skip optional whitespace at s[i]... and return new i.

  Args:
    s: string
    i: int - index into s
  Returns:
    int - index of first none-whitespace character from s[i], or len(s)
  """

  m = _re_wsopt.match(s, i)
  if m:
    return m.end()
  else:
    return i


def _SkipCommaSpace(s, i):
  """Skip optional space with optional comma in it.

  Args:
    s: string
    i: int - index into s
  Returns:
    int - index after optional space with optional comma
  """

  m = _re_wscommaopt.match(s, i)
  if m:
    return m.end()
  else:
    return i
