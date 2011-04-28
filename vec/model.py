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

"""Manipulations of Models.
"""

__author__ = "howard.trickey@gmail.com"

from . import geom
from . import triquad
from . import offset
import math


def PolyAreasToModel(polyareas, bevel_amount, bevel_pitch, quadrangulate):
  """Convert a PolyAreas into a Model object.
  
  Args:
    polyareas: geom.PolyAreas
    bevel_amount: float - if > 0, amount of bevel
    bevel_pitch: float - if > 0, angle in radians of bevel
    quadrangulate: bool - should n-gons be quadrangulated?
  Returns:
    geom.Model
  """

  m = geom.Model()
  if not polyareas:
    return m
  polyareas.points.AddZCoord(0.0)
  m.points = polyareas.points
  for pa in polyareas.polyareas:
    PolyAreaToModel(m, pa, bevel_amount, bevel_pitch, quadrangulate)
  return m


def PolyAreaToModel(m, pa, bevel_amount, bevel_pitch, quadrangulate):
  if bevel_amount > 0.0:
    BevelPolyAreaInModel(m, pa, bevel_amount, bevel_pitch, quadrangulate)
  elif quadrangulate:
    if len(pa.poly) == 0:
      return
    qpa = triquad.QuadrangulateFaceWithHoles(pa.poly, pa.holes, pa.points)
    m.faces.extend(qpa)
    m.colors.extend([ pa.color ] * len(qpa))
  else:
    m.faces.append(pa.poly)
    m.colors.append(pa.color)


def ExtrudePolyAreasInModel(mdl, polyareas, depth, cap_back):
  """Extrude the boundaries given by polyareas by -depth in z.

  Arguments:
    mdl: geom.Model - where to do extrusion
    polyareas: geom.Polyareas
    depth: float
    cap_back: bool - if True, cap off the back
  Side Effects:
    For all edges in polys in polyareas, make quads in Model
    extending those edges by depth in the negative z direction.
    The color will be the color of the face that the edge is part of.
  """

  for pa in polyareas.polyareas:
    back_poly = _ExtrudePoly(mdl, pa.poly, depth, pa.color, True)
    back_holes = []
    for p in pa.holes:
      back_holes.append(_ExtrudePoly(mdl, p, depth, pa.color, False))
    if cap_back:
      qpa = triquad.QuadrangulateFaceWithHoles(back_poly, back_holes,
        polyareas.points)
      # need to reverse each poly to get normals pointing down
      for i, p in enumerate(qpa):
        t = list(p)
        t.reverse()
        qpa[i] = tuple(t)
      model.faces.extend(qpa)
      model.colors.extend([pa.color] * len(qpa))


def _ExtrudePoly(mdl, poly, depth, color, isccw):
  """Extrude the poly by -depth in z

  Arguments:
    mdl: geom.Model - where to do extrusion
    poly: list of vertex indices
    depth: float
    color: tuple of three floats
    isccw: True if counter-clockwise
  Side Effects
    For all edges in poly, make quads in Model
    extending those edges by depth in the negative z direction.
    The color will be the color of the face that the edge is part of.
  Returns:
    list of int - vertices for extruded poly
  """

  if len(poly) < 2:
    return
  extruded_poly = []
  points = mdl.points
  if isccw:
    incr = 1
  else:
    incr = -1
  for i, v in enumerate(poly):
    vnext = poly[(i+incr) % len(poly)]
    (x0,y0,z0) = points.pos[v]
    (x1,y1,z1) = points.pos[vnext]
    vextrude = points.AddPoint((x0,y0,z0-depth))
    vnextextrude = points.AddPoint((x1,y1,z1-depth))
    if isccw:
      sideface = [v, vextrude, vnextextrude, vnext]
    else:
      sideface = [v, vnext, vnextextrude, vextrude]
    mdl.faces.append(sideface)
    mdl.colors.append(color)
    extruded_poly.append(vextrude)
  return extruded_poly


def BevelPolyAreaInModel(mdl, polyarea,
    bevel_amount, bevel_pitch, quadrangulate):
  """Bevel the interior of polyarea in model.

  This does smart beveling: advancing edges are merged
  rather than doing an 'overlap'.  Advancing edges that
  hit an opposite edge result in a split into two beveled areas.

  For now, assume that area is on an xy plane. (TODO: fix)

  Arguments:
    mdl: geom.Model - where to do bevel
    polyarea geom.PolyArea - area to bevel into
    bevel_amount: float - if > 0, amount of bevel
    bevel_pitch: float - if > 0, angle in radians of bevel
    quadrangulate: bool - should n-gons be quadrangulated?
  Side Effects:
    Faces and points are added to model to model the
    bevel and the interior of the polyareas.
  """

  vspeed = math.tan(bevel_pitch)
  off = offset.Offset(polyarea, 0.0)
  off.Build(bevel_amount)
  inner_pas = AddOffsetFacesToModel(mdl, off, vspeed, polyarea.color)
  for pa in inner_pas.polyareas:
    if quadrangulate:
      if len(pa.poly) == 0:
        continue
      qpa = triquad.QuadrangulateFaceWithHoles(pa.poly, pa.holes, pa.points)
      mdl.faces.extend(qpa)
      mdl.colors.extend([ pa.color ] * len(qpa))
    else:
      mdl.faces.append(pa.poly)
      mdl.colors.append(pa.color)


def AddOffsetFacesToModel(mdl, off, vspeed, color = (0.0, 0.0, 0.0)):
  """Add the faces due to an offset into model.

  Returns the remaining interiors of the offset as a PolyAreas.

  Args:
    mdl: geom.Model - model to add offset faces into
    off: offset.Offset
    vspeed: float - vertical speed - how fast height grows with time
    color: (float, float, float) - color to make the faces
  Returns:
    geom.PolyAreas
  """

  mdl.points = off.polyarea.points
  assert(len(mdl.points.pos) == 0 or len(mdl.points.pos[0]) == 3)
  o = off
  ostack = [ ]
  while o:
    if o.endtime != 0.0:
      zouter = o.timesofar * vspeed
      zinner = zouter + o.endtime * vspeed
      for face in o.facespokes:
        n = len(face)
        for i, spoke in enumerate(face):
          nextspoke = face[(i+1) % n]
          v0 = spoke.origin
          v1 = nextspoke.origin
          v2 = nextspoke.dest
          v3 = spoke.dest
          for v in [v0, v1]:
            mdl.points.ChangeZCoord(v, zouter)
          for v in [v2, v3]:
            mdl.points.ChangeZCoord(v, zinner)
          if v2 == v3:
            mface = [v0, v1, v2]
          else:
            mface = [v0, v1, v2, v3]
          mdl.faces.append(mface)
          mdl.colors.append(color)
    ostack.extend(o.inneroffsets)
    if ostack:
      o = ostack.pop()
    else:
      o = None
  return off.InnerPolyAreas()


def BevelSelectionInModel(mdl, selected_faces,
    bevel_amount, bevel_pitch, quadrangulate, as_region):
  """Bevel the selected faces in the model.

  If as_region is False, each face is beveled individually,
  otherwise regions of contiguous faces are merged into
  PolyAreas and beveled as a whole.

  TODO: something if extracted PolyAreas are not approximately
  planar.

  Args:
    mdl: geom.Model
    selected_faces: list of list of int
    bevel_amount: float - amount to inset
    bevel_pitch: float - angle of bevel side
    quadrangulate: bool - should insides be quadrangulated?
    as_region: bool - should faces be merged into regions?
  Side effect:
    Beveling faces will be added to the model
  """

  pas = []
  if as_region:
    pas = RegionToPolyAreas(selected_faces, mdl.points)
  else:
    for face in selected_faces:
      pas.append(geom.PolyArea(mdl.points, face))
  for pa in pas:
    BevelPolyAreaInModel(mdl, pa,
        bevel_amount, bevel_pitch, quadrangulate)


def RegionToPolyAreas(faces, points):
  """Find polygonal outlines induced by union of faces.

  Finds the polygons formed by boundary edges (those not
  sharing an edge with another face in region_faces), and
  turns those into PolyAreas.
  In the general case, there will be holes inside.

  Args:
    faces: list of list of int - each sublist is a face (indices into points)
    points: geom.Points - gives coordinates for vertices
  Returns:
    list of geom.PolyArea
  """

  ans = []
  (edges, vtoe) = _GetEdgeData(faces)
  (face_adj, is_interior_edge) = _GetFaceGraph(faces, edges, vtoe, points)
  (components, ftoc) = _FindFaceGraphComponents(faces, face_adj)
  for c in range(len(components)):
    boundary_edges = set()
    vstobe = dict()
    for e, ((vs, ve), f) in enumerate(edges):
      if ftoc[f] != c or is_interior_edge[e]:
        continue
      boundary_edges.add(e)
      vstobe[vs] = e
    polys = []
    while boundary_edges:
      e = boundary_edges.pop()
      ((vstart, ve), _) = edges[e]
      poly = [ vstart, ve ]
      while ve != vstart:
        if ve not in vstobe:
          print("whoops, couldn't close boundary")
          break
        nexte = vstobe[ve]
        ((_, ve), _) = edges[nexte]
        boundary_edges.remove(nexte)
        if ve != vstart:
          poly.append(ve)
      polys.append(poly)
    if len(polys) == 1:
      ans.append(geom.PolyArea(points, polys[0]))
    else:
      outerf = _FindOuterPoly(polys, points)
      pa = geom.PolyArea(points, polys[outerf])
      pa.holes = [ polys[i] for i in range(len(polys)) if i != outerf ]
      ans.append(pa)
  return ans


def _GetEdgeData(faces):
  """Find edges from faces, and some lookup dictionaries.

  Args:
    faces: list of list of int - each a closed CCW polygon of vertex indices
  Returns:
    (list of ((int, int), int), dict{ int->list of int}) -
      list elements are ((startv, endv), face index)
      dict maps vertices to edge indices
  """

  edges = []
  vtoe = dict()
  for findex, f in enumerate(faces):
    nf = len(f)
    for i, v in enumerate(f):
      endv = f[(i+1) % nf]
      edges.append(((v, endv), findex))
      eindex = len(edges)-1
      if v in vtoe:
        vtoe[v].append(eindex)
      else:
        vtoe[v] = [ eindex ]
  return (edges, vtoe)


def _GetFaceGraph(faces, edges, vtoe, points):
  """Find the face adjacency graph.

  Faces are adjacent if they share an edge,
  and the shared edge goes in the reverse direction,
  and if the angle between them isn't too large.

  Args:
    faces: list of list of int
    edges: list of ((int, int), int) - see _GetEdgeData
    vtoe: dict{ int->list of int } - see _GetEdgeData
    points: geom.Points
  Returns:
    (list of  list of int, list of bool) -
      first list: each sublist is adjacent face indices for each face
      second list: maps edge index to True if it separates adjacent faces
  """

  face_adj = [ [] for i in range(len(faces)) ]
  is_interior_edge = [ False ] * len(edges)
  for e, ((vs, ve), f) in enumerate(edges):
    for othere in vtoe[ve]:
      ((_, we), g) = edges[othere]
      if we == vs:
        # face g is adjacent to face f
        # TODO: angle check
        if g not in face_adj[f]:
          face_adj[f].append(g)
          is_interior_edge[e] = True
        # Don't bother with mirror relations, will catch later
  return (face_adj, is_interior_edge)


def _FindFaceGraphComponents(faces, face_adj):
  """Partition faces into connected components.

  Args:
    faces: list of list of int
    face_adj: list of list of int - see _GetFaceGraph
  Returns:
    (list of list of int, list of int) -
      first list partitions face indices into separate lists, each a component
      second list maps face indices into their component index
  """

  if not faces:
    return ([], [])
  components = []
  ftoc = [ -1 ] * len(faces)
  for i in range(len(faces)):
    if ftoc[i] == -1:
      compi = len(components)
      comp = []
      _FFGCSearch(i, faces, face_adj, ftoc, compi, comp)
      components.append(comp)
  return (components, ftoc)


def _FFGCSearch(findex, faces, face_adj, ftoc, compi, comp):
  """Depth first search helper function for _FindFaceGraphComponents

  Searches recursively through all faces connected to findex, adding
  each face found to comp and setting ftoc for that face to compi.
  """

  comp.append(findex)
  ftoc[findex] = compi
  for otherf in face_adj[findex]:
    if ftoc[otherf] == -1:
      _FFGCSearch(otherf, faces, face_adj, ftoc, compi, comp)

def _FindOuterPoly(polys, points):
  """Assuming polys has one that contains the rest, find that one.

  Args:
    polys: list of list of int - list of polys given by vertex indices
    points: geom.Points
  Returns:
    int - the index in polys of the outermost one
  """

  if len(polys) < 2:
    return 0
  for i, poly in enumerate(polys):
    otherpoly = polys[(i+1) % len(polys)]
    if geom.PointInside(points.pos[otherpoly[0]], poly, points) == 1:
      return i
  print("whoops, couldn't find an outermost poly")
  return 0
