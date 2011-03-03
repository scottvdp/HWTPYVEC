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

"""Convert an Art object to a list of PolyArea objects.
"""

__author__ = "howard.trickey@gmail.com"

from . import geom
from . import vecfile
import itertools


def ArtToPolyAreas(art, subdivide_num, ignore_white = True, combine_paths = False):
  """Convert Art object to PolyAreas.

  Each filled Path in the Art object will produce zero
  or more PolyAreas.

  If ignore_white is True, we assume that white is the background color
  and not intended to produce polyareas (for example, it sometimes there
  is a filled background rectangle for the entire page).

  If combine_paths is True, use the union of all subpaths of all Paths to look for
  outer boundaries and holes, else just look insdie each Path separately.

  Args:
    art: vecfile.Art - contains Paths to convert
    subdivide_num: int - how many times to divide bezier segments
        in order to convert them to line segments.
    ignore_white: bool - if True, ignore white-filled paths
    combine_paths: bool - if True, use union of all Paths in art to
       look for boundaries / holes
  Returns:
    list of geom.PolyArea
  """

  paths_to_convert = filter(
    lambda p: p.filled and p.fillpaint != vecfile.white_paint if ignore_white else True,
    art.paths)
  if combine_paths:
    combinedpath = vecfile.Path()
    combinedpath.subpaths = _flatten([ p.subpaths for p in paths_to_convert ])
    return PathToPolyAreas(combinedpath, subdivide_num)
  else:
    return _flatten([ PathToPolyAreas(p, subdivide_num) for p in paths_to_convert ])


def PathToPolyAreas(path, subdivide_num):
  """Convert Path object to PolyAreas.

  Like ArtToPolyAreas, but for a single Path in Art, and
  we assume that filtering for filled and not being white
  has already been done.

  Usually only one PolyArea will be in the returned list,
  but there may be zero if the path has zero area,
  and there may be more than one if it contains
  non-overlapping polygons.
  (TODO: or if it self-crosses)

  Args:
    path: vecfile.Path - the path to convert
    subdivide_num: int - how many times to divide bezier segments
        in order to convert them to line segments.
  Returns:
    list of geom.PolyArea
  """

  subpolyareas = [ _SubpathToPolyArea(sp, subdivide_num, path.fillpaint) \
      for sp in path.subpaths ]
  return CombineSimplePolyAreas(subpolyareas)


def CombineSimplePolyAreas(subpolyareas):
  """Combine PolyAreas without holes into ones that may have holes.

  Take the poly's in each argument PolyArea and find those that
  are contained in others, so returning a list of PolyAreas that may
  contain holes.
  The argument PolyAreas may be reused an modified in forming
  the result.

  Args:
    subpolyareas: list of geom.PolyArea
  Returns:
    list of geom.PolyArea
  """

  n = len(subpolyareas)
  areas = [ geom.SignedArea(pa.poly, pa.points) for pa in subpolyareas ]
  lens = list(map(lambda x: len(x.poly), subpolyareas))
  cls = dict()
  for i in range(n):
    for j in range(n):
      cls[(i, j)] = _ClassifyPathPairs(subpolyareas[i], subpolyareas[j])
  # calculate set cont where (i,j) is in cont if
  # subpolyareas[i] contains subpolyareas[j]
  cont = set()
  for i in range(n):
    for j in range(n):
      if i != j and _Contains(i, j, areas, lens, cls):
        cont.add((i, j))
  # now make real PolyAreas, with holes assigned
  polyareas = []
  assigned = set()
  count = 0
  while len(assigned) < n and count < n:
    for i in range(n):
      if i in assigned:
        continue
      if _IsBoundary(i, n, cont, assigned):
        # have a new boundary area, i
        assigned.add(i)
        holes = _GetHoles(i, n, cont, assigned)
        pa = subpolyareas[i]
        for j in holes:
          pa.AddHole(subpolyareas[j])
        polyareas.append(pa)
    count += 1
  if len(assigned) < n:
    # shouldn't happen
    print("Whoops, PathToPolyAreas didn't assign all")
  return polyareas


def _SubpathToPolyArea(subpath, subdivide_num, color = (0.0, 0.0, 0.0)):
  """Return a PolyArea representing a single subpath.

  Converts curved segments into approximating line
  segments.
  Ignores zero-length or near zero-length segments.
  Ensures that face is CCW-oriented.

  Args:
    subpath: vecfile.Subpath - the subpath to convert
    subdivide_num: int - how many times to subdivide bezier segments
    color: (float, float, float) - rgb of filling color
  Returns:
    geom.PolyArea
  """

  face = []
  prev = None
  ans = geom.PolyArea()
  ans.color = color
  for seg in subpath.segments:
    (ty, start, end) = seg[0:3]
    if not prev or prev != start:
      face.append(start)
    if ty == "L":
      face.append(end)
      prev = end
    elif ty == "B":
      approx = Bezier3Approx([start, seg[3], seg[4], end], subdivide_num)
      # first point of approx should be current end of face
      face.extend(approx[1:])
      prev = end
    elif ty == "Q":
      print("unimplemented segment type Q")
    else:
      print("unexpected segment type", ty)
  # now make a cleaned face in a new PolyArea
  # with no two successive points approximately equal
  # and a new vmap
  if len(face) <= 2:
    # degenerate face, return an empty PolyArea
    return ans
  previndex = -1
  for i in range(0, len(face)):
    point = face[i]
    newindex = ans.points.AddPoint(point)
    if newindex == previndex or \
        i == len(face)-1 and newindex == ans.poly[0]:
      continue
    ans.poly.append(newindex)
    previndex = newindex
  # make sure that face is CCW oriented
  if geom.SignedArea(ans.poly, ans.points) < 0.0:
    ans.poly.reverse()
  return ans


def Bezier3Approx(cps, subdivide_num):
  """Compute a polygonal approximation to a cubic bezier segment.

  Args:
    cps: list of 4 coord tuples - (start, control point 1, control point 2, end)
    subdivide_num: int - how many times to subdivide bezier segments
  Returns:
    list of tuples (coordinates) for straight line approximation of the bezier
  """

  (vs, _, _, ve) = b0 = cps
  if subdivide_num == 0:
    return [vs, ve]
  alpha = 0.5
  b1 = _Bez3step(b0, 1, alpha)
  b2 = _Bez3step(b1, 2, alpha)
  b3 = _Bez3step(b2, 3, alpha)
  if subdivide_num == 1:
    # recursive case would do this too, but optimize a bit
    return [vs, b3[0], ve]
  else:
    left = [b0[0], b1[0], b2[0], b3[0]]
    right = [b3[0], b2[1], b1[2], b0[3]]
    ansleft = Bezier3Approx(left, subdivide_num-1)
    ansright = Bezier3Approx(right, subdivide_num-1)
    # ansleft ends with b3[0] and ansright starts with it
    return ansleft + ansright[1:]


def _Bez3step(b, r, alpha):
  """Cubic bezier step r for interpolating at parameter alpha.

  Steps 1, 2, 3 are applied in succession to the 4 points
  representing a bezier segment, making a triangular arrangement
  of interpolating the previous step's output, so that after
  step 3 we have the point that is at parameter alpha of the segment.
  The left-half control points will be on the left side of the triangle
  and the right-half control points will be on the right side of the triangle.

  Args:
    b: list of tuples (coordinates), of length 5-r
    r: int - step number (0=orig points and cps)
    alpha: float - value in range 0..1 where want to divide at
  Returns:
    list of length 4-r, of vertex coordinates, giving linear interpolations
        at parameter alpha between successive pairs of points in b
  """

  ans = []
  n = len(b[0])  # dimension of coordinates
  beta = 1-alpha
  for i in range(0, 4-r):
    # find c, alpha of the way from b[i] to b[i+1]
    t = [0.0] * n
    for d in range(n):
      t[d] = b[i][d] * beta + b[i+1][d] * alpha
    ans.append(tuple(t))
  return ans


def _ClassifyPathPairs(a, b):
  """Classify vertices of path b with respect to path a.

  Args:
    a: geom.PolyArea - the test outer face (ignoring holes)
    b: geom.PolyArea - the test inner face (ignoring holes)
  Returns:
    (int, int) - first is #verts of b inside a, second is #verts of b on a
  """

  num_in = 0
  num_on = 0
  for v in b.poly:
    vp = b.points.pos[v]
    k = geom.PointInside(vp, a.poly, a.points)
    if k > 0:
      num_in += 1
    elif k == 0:
      num_on += 1
  return (num_in, num_on)


def _Contains(i, j, areas, lens, cls):
  """Return True if path i contains majority of vertices of path j.

  Args:
    i: index of supposed containing path
    j: index of supposed contained path
    areas: list of floats - areas of all the paths
    lens: list of ints - lenths of each of the paths
    cls: dict - maps pairs to result of _ClassifyPathPairs
  Returns:
    bool - True if path i contains at least 55% of j's vertices
  """

  if i == j:
    return False
  (jinsidei, joni) = cls[(i, j)]
  if jinsidei == 0 or joni == lens[j] or \
     float(jinsidei)/float(lens[j]) < 0.55:
    return False
  else:
    (insidej, _) = cls[(j, i)]
    if float(insidej) / float(lens[i]) > 0.55:
      return areas[i] > areas[j]  # tie breaker
    else:
      return True


def _IsBoundary(i, n, cont, assigned):
  """Is path i a boundary, given current assignment?

  Args:
    i: int - index of a path to test for boundary possiblity
    n: int - total number of paths
    cont: dict - maps path pairs (i,j) to _Contains(i,j,...) result
    assigned: set  of int - which paths are already assigned
  Returns:
    bool - True if there is no unassigned j, j!=i, such that
           path j contains path i
  """

  for j in range(0, n):
    if j == i or j in assigned:
      continue
    if (j,i) in cont:
      return False
  return True


def _GetHoles(i, n, cont, assigned):
  """Find holes for path i: i.e., unassigned paths directly inside it.

  Directly inside means there is not some other unassigned path k
  such that path such that path i contains k and path k contains j.
  (If such a k is already assigned, then its islands have been assigned too.)

  Args:
    i: int - index of a boundary path
    n: int - total number of paths
    cont: dict - maps path pairs (i,j) to _Contains(i,j,...) result
    assigned: set  of int - which paths are already assigned
  Returns:
    list of int - indices of paths that are islands
  Side Effect:
    Adds island indices to assigned set.
  """

  isls = []
  for j in range(0, n):
    if j in assigned:
      continue   # catches i==j too, since i is assigned by now
    if (i, j) in cont:
      directly = True
      for k in range(0, n):
        if k == j or k in assigned:
          continue
        if (i, k) in cont and (k, j) in cont:
          directly = False
          break
      if directly:
        isls.append(j)
        assigned.add(j)
  return isls


def _flatten(l):
  """Return a flattened shallow list.

  Args:
    l : list of lists
  Returns:
    list - concatenation of sublists of l
  
  """

  return list(itertools.chain.from_iterable(l))


