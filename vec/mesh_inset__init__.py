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
  "location": "View3D > Toolbar and View3D > Specials (W-key)",
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
    ob = context.active_object
    return (ob and ob.type == 'MESH' and context.mode == 'EDIT_MESH')

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
    return


class VIEW3D_PT_tools_inset(bpy.types.Panel):
  bl_space_type = 'VIEW_3D'
  bl_region_type = 'TOOLS'
  bl_context = "mesh_edit"
  bl_label = "Inset"

  def draw(self, context):
    layout = self.layout
    layout.operator("mesh.inset", text="Inset")


def register():
  bpy.utils.register_class(Inset)
  bpy.utils.register_class(VIEW3D_PT_tools_inset)


def unregister():
  bpy.utils.unregister_class(Inset)
  bpy.utils.unregister_class(Inset)


if __name__ == "__main__":
  register()
