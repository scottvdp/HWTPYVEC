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
from . import vecfile


def ParseSVGFile(filename):
  """Parse an SVG file name and return an Art object for it.

  Args:
    filename: string - name of file to read and parse
  Returns:
    vecfile.Art
  """

  dom = xml.dom.minidom.parse(filename)
  return _SVGDomToArt(dom)


def ParseSVGString(s):
  """Parse an SVG string and return an Art object for it.

  Args:
    s: string - contains svg
  Returns:
    vecfile.Art
  """

  dom = xml.dom.minidom.parseString(s)
  return _SVGDomToArg(dom)


def _SVGDomToArt(dom):
  """Convert an svg file in dom form into an Art object.

  Args:
    dom: xml.dom.minidom.Document
  Returns:
    vecfile.Art
  """

  art = vecfile.Art()
  gs = vecfile.GState()
  svgs = dom.getElementsByTagName('svg')
  if len(svgs) == 0:
    return art
  svg = svgs[0]
  _ProcessChildren(svgs[0], art, gs)
  return art


def _ProcessChildren(nodes, art, gs):
  """Process a list of SVG nodes, updating art.

  Args:
    nodes: list of xml.dom.Node
    art: vecfile.Art
    gs: vecfile.GState
  Side effects:
    Maybe adds paths to art.
  """

  for node in nodes.childNodes:
    _ProcessNode(node, art, gs)


def _ProcessNode(node, art, gs):
  """Process an SVG node, updating art.

  Args:
    node: xml.dom.Node
    art: vecfile.Art
    gs: vecfile.GState
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
    pass  # TODO
  elif tag == 'polygon':
    if node.hasAttribute('points'):
      coords = _ParseCoordPairList(node.getAttribute('points'))
      n = len(coords)
      if n > 0:
        sp = vecfile.Subpath()
        sp.segments = [ ('L', coords[i], coords[i % n]) for i in range(n) ]
        sp.closed = True
        path = vecfile.Path()
        _SetPathAttributes(path, node, gs)
        path.subpaths = [ sp ]
        art.paths.append(path)
  elif tag == 'rect':
    pass  # TODO
  elif tag == 'ellipse':
    pass  # TODO


def _SetPathAttributes(path, node, gs):
  """Set the attributes related to filling/stroking in path.

  Use attribute settings in node, if there, else those in the
  current graphics state, gs.

  Arguments:
    path: vecfile.Path
    node: xml.dom.Node
    gs: vecfile.GState
  Side effects:
    May set filled, fillevenodd, stroked, fillpaint, strokepaint in path.
  """

  if node.hasAttribute('fill'):
    path.fillpaint = _ParsePaint(node.getAttribute('fill'))
    if path.fillpaint:
      path.filled = True
  if node.hasAttribute('stroke'):
    path.strokepaint = _ParsePaint(node.getAttribute('stroke'))
    if path.strokepaint:
      path.stroked = True
  if node.hasAttribute('fill-rule'):
    path.fillevenodd = node.getAttribute('fill-rule') == 'evenodd'

# Some useful regular expressions
_re_float = re.compile(r"((\+|-)?([0-9]+\.[0-9]*)|(\.[0-9]+)|([0-9]+))")
_re_int = re.compile(r"(\+|-)?[0-9]+")
_re_wsopt = re.compile(r"\s*")
_re_wscomma = re.compile(r"(\s*,\s*)|(\s+)")

def _ParsePaint(s):
  """Parse an SVG paint definition and return our version of Paint.

  If fail to parse, or the color is 'none', return None.

  Args:
    s: string - should contain an SVG paint spec
  Returns:
    vecfile.Paint or None
  """

  if len(s) == 0 or s == 'none':
    return None
  if s[0] == '#':
    if len(s) == 7:
      # 6 hex digits
      return vecfile.Paint( \
        int(s[1:3], 16) / 255.0,
        int(s[3:5], 16) / 255.0,
        int(s[5:7], 16) / 255.0)
    elif len(s) == 4:
      # 3 hex digits
      return vecfile.Paint( \
        int(s[1], 16)*17 / 255.0,
	int(s[2], 16)*17 / 255.0,
	int(s[3], 16)*17 / 255.0)
  else:
    if s in _ColorDict:
      return _ColorDict[s]
  return None

_ColorDict = {
  'aqua' : vecfile.Paint(0.0, 1.0, 1.0),
  'black' : vecfile.Paint(0.0, 0.0, 0.0),
  'blue' : vecfile.Paint(0.0, 0.0, 1.0),
  'fuchsia' : vecfile.Paint(1.0, 0.0, 1.0),
  'gray' : vecfile.Paint(0.5, 0.5, 0.5),
  'green' : vecfile.Paint(0.0, 0.5, 0.0),
  'lime' : vecfile.Paint(0.0, 1.0, 0.0),
  'maroon' : vecfile.Paint(0.5, 0.0, 0.0),
  'navy' : vecfile.Paint(0.0, 0.0, 0.5),
  'olive' : vecfile.Paint(0.5, 0.5, 0.0),
  'purple' : vecfile.Paint(0.5, 0.0, 0.5),
  'red' : vecfile.Paint(1.0, 0.0, 0.0),
  'silver' : vecfile.Paint(0.75, 0.75, 0.75),
  'teal' : vecfile.Paint(0.0, 0.5, 0.5),
  'white' : vecfile.Paint(1.0, 1.0,1.0),
  'yellow' : vecfile.Paint(1.0, 1.0, 0.0)
}


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
  i = 0
  prev = None
  m = _re_wsopt.match(s, i)
  if m:
    i = m.end()
  while i < len(s):
    m = _re_float.match(s, i)
    if m:
      v = float(m.group())
      if prev:
        ans.append((prev, v))
        prev = None
      else:
        prev = v
      i = m.end()
    else:
      break
    m = _re_wscomma.match(s, i)
    if not m:
      break
    i = m.end()
  return ans

