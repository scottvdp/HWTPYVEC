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

__author__ = ["Howard Trickey"]
__version__ = '0.1'
__bpydoc__ = """\
This script imports various vector format files to Blender.
Currently it handles Adobe Illustrator, PDF, and some EPS files.

It had two modes of finding polygons: the first is to simply
look for filled polygons (not filled with white, which is usually
the background) and import those.
The other is to look at the union of all closed polygons and
assume that containment = holes.


Usage:<br>
    Execute this script from the "File->Import" menu and choose a vector
file to open.
"""

import bpy
from bpy.props import *
from . import model

class VectorImporter(bpy.types.Operator):
  '''Load Vector file as mesh data'''
  bl_idname = "import_mesh.vector"
  bl_label = "Import vector"
  bl_description = "Imports Vector Art as polygons into 3D Scenes"
  bl_options = {'REGISTER', 'UNDO'}
    
  filepath = StringProperty(name="File Path", description="Filepath used for importing the vector file",
      maxlen=1024, default="", subtype='FILE_PATH')
  subdivides = IntProperty(name="Number of subdivides",
      description="Number of times to subdivide curves",
      default = 1,
      min = 0,
      max = 10)
  scale = FloatProperty(name="Scale",
      description="Scale longer bounding box side to this size",
      default=4.0,
      min=0.1,
      max=100.0,
      unit="LENGTH")
  adaptive = BoolProperty(name="Adaptive subdivide",
      description="Use adaptive subdivision for curves",
      default=False)

  def draw(self, context):
    layout = self.layout
    box = layout.box()
    box.label("Import Options")
    box.prop(self, "subdivides")
    box.prop(self, "scale")
    # box.prop(self, "adaptive")

  def execute(self, context):
    # self.report({'WARNING'}, 'filepath=' + self.filepath)
    #convert the filename to an object name
    objname = bpy.path.display_name(self.filepath.split("\\")[-1].split("/")[-1])

    (mdl, msg) = model.ReadVecFileToModel(self.filepath, True, self.subdivides, self.scale)
    if msg:
      self.report({'ERROR'}, 'Problem reading file ' + self.filepath + ': ' + msg)
      return {'FINISHED'}
    verts = mdl.points.pos
    faces = mdl.faces
    mesh = bpy.data.meshes.new(objname)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(objname, mesh)
    context.scene.objects.link(obj)
    bpy.ops.object.select_all(action = "DESELECT")
    obj.select = True
    context.scene.objects.active = obj

    return {'FINISHED'}

  def invoke(self, context, event):
    wm = context.window_manager
    wm.fileselect_add(self)
    return {'RUNNING_MODAL'}
