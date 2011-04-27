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

bl_info = {
  "name": "Inset Polygon",
  "author": "Howard Trickey",
  "version": (0, 1),
  "blender": (2, 5, 7),
  "api": 36147,
  "location": "View3D > Tools",
  "description": "Make an inset polygon inside selection.",
  "warning": "",
  "wiki_url": "",
  "tracker_url": "",
  "category": "Mesh"}

if "bpy" in locals():
  import imp
else:
  from . import geom
  from . import model
  from . import offset
  from . import triquad

import math
import bpy
import mathutils
from bpy.props import *


class Inset(bpy.types.Operator):
  bl_idname = "mesh.inset"
  bl_label = "Inset"
  bl_description = "Make an inset polygon inside selection"
  bl_options = {'REGISTER', 'UNDO'}

  inset_amount = FloatProperty(name="Amount",
    description="Distance of inset edges from outer ones",
    default = 0.0,
    min = 0.0,
    max = 1000.0,
    unit = 'LENGTH')
  inset_height = FloatProperty(name="Height",
    description="Distance to raise inset faces",
    default = 0.0,
    min = -1000.0,
    max = 1000.0,
    unit = 'LENGTH')

  @classmethod
  def poll(cls, context):
    obj = context.active_object
    return (obj and obj.type == 'MESH' and context.mode == 'EDIT_MESH')

  def draw(self, context):
    layout= self.layout
    box = layout.box()
    box.label("Inset Options")
    box.prop(self, "inset_amount")
    box.prop(self, "inset_height")

  def invoke(self, context, event):
    self.action(context)
    return {'FINISHED'}

  def execute(self, context):
    self.action(context)
    return {'FINISHED'}

  def action(self, context):
    save_global_undo = bpy.context.user_preferences.edit.use_global_undo
    bpy.context.user_preferences.edit.use_global_undo = False
    bpy.ops.object.mode_set(mode='OBJECT')
    obj = bpy.context.active_object
    mesh = obj.data
    do_inset(mesh, self.inset_amount, self.inset_height)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.context.user_preferences.edit.use_global_undo = save_global_undo


def do_inset(mesh, amount, height):
  if amount <= 0.0:
    return
  pitch = math.atan(height / amount)
  selfaces = []
  for face in mesh.faces:
    if face.select and not face.hide:
      selfaces.append(face)
  m = geom.Model()
  # if add all mesh.vertices, coord indices will line up
  for v in mesh.vertices:
    k = m.points.AddPoint(v.co.to_tuple())
  for f in selfaces:
    m.faces.append(list(f.vertices))
  orig_numv = len(m.points.pos)
  orig_numf = len(m.faces)
  pas = model.RegionToPolyAreas(f.faces, points)
  for pa in pas:
    model.BevelPolyAreaInModel(m, pa, amount, pitch, True)
  # blender_faces: newfaces but all 4-tuples and no 0
  # in 4th position if a 4-sided poly
  blender_faces = []
  for i in range(orig_numf, len(m.faces)):
    f = m.faces[i]
    if len(f) == 3:
      blender_faces.append(f + [0])
    elif len(f) == 4:
      if f[3] == 0:
        blender_faces.append([f[3], f[0], f[1], f[2]])
      else:
        blender_faces.append(f)
  num_new_vertices = len(m.points.pos) - orig_numv
  mesh.vertices.add(num_new_vertices)
  for i in range(orig_numv, len(m.points.pos)):
    mesh.vertices[i].co = mathutils.Vector(m.points.pos[i])
  start_faces = len(mesh.faces)
  mesh.faces.add(len(blender_faces))
  for i, newf in enumerate(blender_faces):
    mesh.faces[start_faces + i].vertices_raw = newf
  mesh.update(calc_edges = True)
  # remove original faces
  bpy.context.tool_settings.mesh_select_mode = [False, False, True]
  bpy.ops.object.mode_set(mode = 'EDIT')
  bpy.ops.mesh.select_all(action = 'DESELECT')
  bpy.ops.object.mode_set(mode = 'OBJECT')
  for f in selfaces:
    f.select = True
  bpy.ops.object.mode_set(mode = 'EDIT')
  bpy.ops.mesh.delete(type = 'FACE')



def panel_func(self, context):
  self.layout.label(text="Inset:")
  self.layout.operator("mesh.inset", text="Inset")


def register():
  bpy.utils.register_class(Inset)
  bpy.types.VIEW3D_PT_tools_meshedit.append(panel_func)


def unregister():
  bpy.utils.unregister_class(Inset)
  bpy.types.VIEW3D_PT_tools_meshedit.remove(panel_func)


if __name__ == "__main__":
  register()
