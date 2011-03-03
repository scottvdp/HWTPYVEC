import bpy

context = bpy.context
scene = context.scene
mesh = bpy.data.meshes.new("tetra")
verts = [(0.0, 0.0, 0.0),
         (1.0, 0.0, 0.0),
         (0.0, 1.0, 0.0),
         (1.0, 1.0, 0.0),
         (0.5, 0.5, 1.0)]
faces = [(0,1,2,3), (0,1,4), (1,2,4), (2,3,4), (3,0,4)]
mesh.from_pydata(verts, [], faces)
mesh.update()
