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

  def bounds(self):
    """Find bounding box of model. 

    Returns:
      ([minx,miny,minz],[maxx,maxy,maxz])
    """

    huge = 1e100
    minv = [huge, huge, huge]
    maxv = [-huge, -huge, -huge]
    for face in self.faces:
      for v in face:
        vcoords = self.points.pos[v]
        for i in range(3):
          if vcoords[i] < minv[i]:
            minv[i] = vcoords[i]
          if vcoords[i] > maxv[i]:
            maxv[i] = vcoords[i]
    if minv[0] == huge:
      minv = [0.0, 0.0, 0.0]
    if maxv[0] == huge:
      maxv = [0.0, 0.0, 0.0]
    return (minv, maxv)

  def scale_and_center(self, scaled_side_target):
    """Adjust the coordinates of the model so that
    it is centered at the origin and has its longest
    dimension scaled to be scaled_side_target."""

    (minv, maxv) = self.bounds()
    maxside = max([ maxv[i]-minv[i] for i in range(3) ])
    if maxside > 0.0:
      scale = scaled_side_target / maxside
    else:
      scale = 1.0
    translate = [ -0.5*(maxv[i]+minv[i]) for i in range(3) ]
    for v in range(len(self.points.pos)):
      self.points.pos[v] = [ scale*(self.points.pos[v][i] + translate[i]) for i in range(3) ]

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
  """

  def __init__(self):
    self.quadrangulate = True
    self.convert_options = art2polyarea.ConvertOptions()
    self.scaled_side_target = 4.0
    self.extrude_depth = 0.0
    self.bevel_amount = 0.0
    self.bevel_pitch = 0.0


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
    art: vecfile.Art - the Art object to convert.
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

  We apply scale_and_center to the model before returning,
  using options.scaled_side_target, if it is greater than 0.

  Args:
    polyareas: geom.PolyAreas
    options: ImportOptions
  Returns:
    Model
  """

  m = Model()
  if not polyareas:
    return m
  pfaces = []
  pcolors = []
  m.points = polyareas.points
  for pa in polyareas.polyareas:
    if options.quadrangulate:
      if len(pa.poly) == 0:
        continue
      if not pa.holes:
        qpa = triquad.QuadrangulateFace(pa.poly, pa.points)
      else:
        qpa = triquad.QuadrangulateFaceWithHoles(pa.poly, pa.holes, pa.points)
      pfaces.extend(qpa)
      pcolors.extend([ pa.color ] * len(qpa))
    else:
      pfaces.append(pa.poly)
      pcolors.append(pa.color)
  m.faces = pfaces
  m.colors = pcolors
  if len(m.points.pos) > 0 and len(m.points.pos[0]) == 2:
    m.points = m.points.AddZCoord(0.0)
  if options.scaled_side_target > 0:
    m.scale_and_center(options.scaled_side_target)
  if options.extrude_depth > 0:
    ExtrudePolyAreasInModel(m, polyareas, options.extrude_depth)
  return m


def OffsetToModel(off, vspeed, quadrangulate):
  """Convert an Offset object into a Model object.

  Args:
    off: offset.Offset
    vspeed: float - vertical speed - how fast height grows with time
    quadrangulate: bool - if True quandrangulate any ngons
  Returns:
    Model
  """

  m = Model()
  m.points = off.polyarea.points
  if len(m.points.pos) > 0 and len(m.points.pos[0]) == 2:
    m.points = m.points.AddZCoord(0.0)
  o = off
  ostack = [ ]
  while o:
    if o.endtime == 0.0:
      _MakeInnerFacesOffsetModel(m, o, quadrangulate)
    else:
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
    ostack.extend(o.inneroffsets)
    if ostack:
      o = ostack.pop()
    else:
      o = None
  return m


def _MakeInnerFacesOffsetModel(model, off, quadrangulate):
  """Make the inner faces, given by off, of model.
  """

  # TODO
  pass


def ExtrudePolyAreasInModel(model, polyareas, depth):
  """Extrude the boundaries given by polyareas by -depth in z.

  Arguments:
    model: Model - where to do extrusion
    polyareas: geom.Polyareas
    depth: float
  Side Effects:
    For all edges in polys in polyareas, make quads in Model
    extending those edges by depth in the negative z direction.
    The color will be the color of the face that the edge is part of.
  """

  for pa in polyareas.polyareas:
    _ExtrudePoly(model, pa.poly, depth, pa.color, True)
    for p in pa.holes:
      _ExtrudePoly(model, p, depth, pa.color, False)


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
  """

  if len(poly) < 2:
    return
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


