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
  opt = model.ImportOptions()
  opt.bevel_amount = amount
  opt.bevel_pitch = math.atan(height / amount)
  faces = []
  for face in mesh.faces:
    if face.select and not face.hide:
      faces.append(face)
  m = model.Model()
  # if add all mesh.vertices, coord indices will line up
  for v in mesh.vertices:
    k = m.points.AddPoint(v.co.to_tuple())
  if len(faces) == 1:
    f = faces[0]
    fverts = list(f.vertices)  # indices into mesh.vertices
    m.faces.append(fverts)
    print("m.faces", m.faces)
    pa = geom.PolyArea(m.points, fverts)
    model.BevelPolyAreaInModel(m, pa, opt)
    # make sure faces don't end in index 0
    for i, newf in enumerate(m.faces):
      if newf[-1] == 0:
        if newf[0] == 0:
          m.faces[i] = [newf[1], newf[2], newf[3], newf[1]]
        else:
          m.faces[i] = [newf[-1]] + newf[:-1]
    start_vertices = len(mesh.vertices)
    num_new_vertices = len(m.points.pos) - start_vertices
    mesh.vertices.add(num_new_vertices)
    for i in range(start_vertices, len(m.points.pos)):
      mesh.vertices[i].co = mathutils.Vector(m.points.pos[i])
    start_faces = len(mesh.faces)
    mesh.faces.add(len(m.faces))
    for i, newf in enumerate(m.faces):
      mesh.faces[start_faces + i].vertices_raw = newf
    mesh.update(calc_edges = True)


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
