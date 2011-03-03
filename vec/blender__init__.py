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

bl_addon_info = {
  "name": "Vector import",
  "author": "Howard Trickey",
  "version": (0, 1),
  "blender": (2, 5, 6),
  "api": 31667,
  "location": "File > Import-Export > Vector ",
  "description": "Import Vector Files (.ai, .pdf)",
  "warning": "",
  "wiki_url": "",
  "tracker_url": "",
  "category": "Import-Export"}

if "bpy" in locals():
  from imp import reload
  if "import_vector" in locals():
    reload(import_vector)
  if "geom" in locals():
    reload(geom)
  if "model" in locals():
    reload(model)
  if "vecfile" in locals():
    reload(vecfile)
  if "pdf" in locals():
    reload(pdf)
  if "triquad" in locals():
    reload(triquad)
  if "arg2polyarea" in locals():
    reload(art2polyarea)
else:
  from . import import_vector
  from . import geom
  from . import model
  from . import vecfile
  from . import pdf
  from . import triquad
  from . import art2polyarea


import bpy

def menu_import(self, context):
  self.layout.operator(import_vector.VectorImporter.bl_idname, text="Vector files (.ai, .pdf)").filepath = "*.ai, *.pdf"

def register():
  # register_module was added only recently, but seems mandatory now
  if 'register_module' in dir(bpy.utils):
    bpy.utils.register_module(__name__)
  bpy.types.INFO_MT_file_import.append(menu_import)

def unregister():
  if 'unregister_module' in dir(bpy.utils):
    bpy.utils.unregister_module(__name__)
  bpy.types.INFO_MT_file_import.remove(menu_import)

if __name__ == "__main__":
  register()
