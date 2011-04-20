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

"""Converting 2d vector art to 3d models.

This is a generic converter, with a sample output
to .obj format.
"""

__author__ = "howard.trickey@gmail.com"

from . import geom
from . import vecfile
from . import art2polyarea
from . import triquad
from . import offset
import math

class Model(object):
  """Contains a generic 3d model.

  A generic 3d model has vertices with 3d coordinates.
  Each vertex gets a 'vertex id', which is an index that
  can be used to refer to the vertex and can be used
  to retrieve the 3d coordinates of the point.

  The actual visible part of the geometry are the faces,
  which are n-gons (n>2), specified by a vector of the
  n corner vertices.
  Faces may also have colors.

  Attributes:
    points: geom.Points - the 3d vertices
    faces: list of list of indices (each a CCW traversal of a face)
    colors: list of (float, float, float) - if present, is parallel to 
        faces list and gives rgb colors of faces
  """

  def __init__(self):
    self.points = geom.Points()
    self.faces = []
    self.colors = []

  def writeObjFile(self, fname):
    """Write the model as a .obj format file.

    Args:
      fname: filename to write to
    """

    f = open(fname, "w")
    for i in range(0, len(self.points.pos)):
      f.write("v %f %f %f\n" % tuple(self.points.pos[i]))
    for face in self.faces:
      f.write("f")
      for v in face:
        f.write(" %d" % (v+1))  # .obj vertices start at 1
      f.write("\n")
    f.close()

class ImportOptions(object):
  """Contains options used to control model import.

  Attributes:
    quadrangulate: bool - should n-gons be quadrangulated?
    convert_options: art2polyarea.ConvertOptions -
      options about how to convert vector files into
      polygonal areas
    scaled_side_target: float - scale model so that longest side
      is this length, if > 0.
    extrude_depth: float - if > 0, extrude polygons up by this amount
    bevel_amount: float - if > 0, inset polygons by this amount
    bevel_pitch: float - if > 0, angle in radians of bevel
    cap_back: bool - should we cap the back, if extruding?
  """

  def __init__(self):
    self.quadrangulate = True
    self.convert_options = art2polyarea.ConvertOptions()
    self.scaled_side_target = 4.0
    self.extrude_depth = 0.0
    self.bevel_amount = 0.0
    self.bevel_pitch = 45.0 * math.pi / 180.0
    self.cap_back = False


def ReadVecFileToModel(fname, options):
  """Read vector art file and convert to Model.

  Args:
    fname: string - the file to read
    options: ImportOptions - specifies some choices about import
  Returns:
    (Model, string): if there was a major problem, Model may be None.
      The string will be errors and warnings.
  """

  art = vecfile.ParseVecFile(fname)
  if art is None:
    return (None, "Problem reading file or unhandled type")
  return ArtToModel(art, options)


def ArtToModel(art, options):
  """Convert an Art object into a Model object.

  Args:
    art: geom.Art - the Art object to convert.
    options: ImportOptions - specifies some choices about import
  Returns:
    (Model, string): if there was a major problem, Model may be None.
      The string will be errors and warnings.
  """

  pareas = art2polyarea.ArtToPolyAreas(art, options.convert_options)
  if not pareas:
    return (None, "No visible faces found")
  model = PolyAreasToModel(pareas, options)
  return (model, "")


def PolyAreasToModel(polyareas, options):
  """Convert a PolyAreas into a Model object.
  
  Args:
    polyareas: geom.PolyAreas
    options: ImportOptions
  Returns:
    Model
  """

  m = Model()
  if not polyareas:
    return m
  if options.scaled_side_target > 0:
    polyareas.scale_and_center(options.scaled_side_target)
  polyareas.points.AddZCoord(0.0)
  m.points = polyareas.points
  for pa in polyareas.polyareas:
    _PolyAreaToModel(m, pa, options)
  if options.extrude_depth > 0:
    ExtrudePolyAreasInModel(m, polyareas, options.extrude_depth,
      options.cap_back)
  return m


def _PolyAreaToModel(m, pa, options):
  if options.bevel_amount > 0.0:
    BevelPolyAreaInModel(m, pa, options)
  elif options.quadrangulate:
    if len(pa.poly) == 0:
      return
    qpa = triquad.QuadrangulateFaceWithHoles(pa.poly, pa.holes, pa.points)
    m.faces.extend(qpa)
    m.colors.extend([ pa.color ] * len(qpa))
  else:
    m.faces.append(pa.poly)
    m.colors.append(pa.color)


def ExtrudePolyAreasInModel(model, polyareas, depth, cap_back):
  """Extrude the boundaries given by polyareas by -depth in z.

  Arguments:
    model: Model - where to do extrusion
    polyareas: geom.Polyareas
    depth: float
    cap_back: bool - if True, cap off the back
  Side Effects:
    For all edges in polys in polyareas, make quads in Model
    extending those edges by depth in the negative z direction.
    The color will be the color of the face that the edge is part of.
  """

  for pa in polyareas.polyareas:
    back_poly = _ExtrudePoly(model, pa.poly, depth, pa.color, True)
    back_holes = []
    for p in pa.holes:
      back_holes.append(_ExtrudePoly(model, p, depth, pa.color, False))
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


def _ExtrudePoly(model, poly, depth, color, isccw):
  """Extrude the poly by -depth in z

  Arguments:
    model: Model - where to do extrusion
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
  points = model.points
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
    model.faces.append(sideface)
    model.colors.append(color)
    extruded_poly.append(vextrude)
  return extruded_poly


def BevelPolyAreaInModel(model, polyarea, options):
  """Bevel the interior of polyarea in model.

  This does smart beveling: advancing edges are merged
  rather than doing an 'overlap'.  Advancing edges that
  hit an opposite edge result in a split into two beveled areas.

  For now, assume that area is on an xy plane. (TODO: fix)

  Arguments:
    model: Model - where to do bevel
    polyarea geom.PolyArea - area to bevel into
    options: ImportOptions
  Side Effects:
    Faces and points are added to model to model the
    bevel and the interior of the polyareas.
    Any faces that currently filled those areas are
    deleted (TODO).
  """

  vspeed = math.tan(options.bevel_pitch)
  off = offset.Offset(polyarea, 0.0)
  off.Build(options.bevel_amount)
  inner_pas = AddOffsetFacesToModel(model, off, vspeed, polyarea.color)
  for pa in inner_pas.polyareas:
    if options.quadrangulate:
      if len(pa.poly) == 0:
        continue
      qpa = triquad.QuadrangulateFaceWithHoles(pa.poly, pa.holes, pa.points)
      model.faces.extend(qpa)
      model.colors.extend([ pa.color ] * len(qpa))
    else:
      model.faces.append(pa.poly)
      model.colors.append(pa.color)


def AddOffsetFacesToModel(m, off, vspeed, color = (0.0, 0.0, 0.0)):
  """Add the faces due to an offset into model.

  Returns the remaining interiors of the offset as a PolyAreas.

  Args:
    m: model to add offset faces into
    off: offset.Offset
    vspeed: float - vertical speed - how fast height grows with time
    color: (float, float, float) - color to make the faces
  Returns:
    geom.PolyAreas
  """

  m.points = off.polyarea.points
  assert(len(m.points.pos) == 0 or len(m.points.pos[0]) == 3)
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
            m.points.ChangeZCoord(v, zouter)
          for v in [v2, v3]:
            m.points.ChangeZCoord(v, zinner)
          if v2 == v3:
            mface = [v0, v1, v2]
          else:
            mface = [v0, v1, v2, v3]
          m.faces.append(mface)
          m.colors.append(color)
    ostack.extend(o.inneroffsets)
    if ostack:
      o = ostack.pop()
    else:
      o = None
  return off.InnerPolyAreas()
