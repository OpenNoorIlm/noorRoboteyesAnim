import bpy
import numpy as np

obj = bpy.data.objects["Eyes"]
mesh = obj.data

# 1. Store shape key data
key_blocks = mesh.shape_keys.key_blocks
key_names = [kb.name for kb in key_blocks]
key_values = [kb.value for kb in key_blocks]
key_mins = [kb.slider_min for kb in key_blocks]
key_maxs = [kb.slider_max for kb in key_blocks]
orig_vert_count = len(mesh.vertices)

all_coords = []
for kb in key_blocks:
    coords = np.zeros(orig_vert_count * 3, dtype=np.float32)
    kb.data.foreach_get("co", coords)
    all_coords.append(coords.reshape(-1, 3))

basis_orig = all_coords[0]

# 2. Temporarily hide subdiv so depsgraph only bakes mirror
subsurf_settings = []
for mod in obj.modifiers:
    if mod.type == 'SUBSURF':
        subsurf_settings.append({
            "name": mod.name,
            "levels": mod.levels,
            "render_levels": mod.render_levels,
            "show_viewport": mod.show_viewport
        })
        mod.show_viewport = False

depsgraph = bpy.context.evaluated_depsgraph_get()
obj_eval = obj.evaluated_get(depsgraph)
new_mesh = bpy.data.meshes.new_from_object(obj_eval)
new_vert_count = len(new_mesh.vertices)

print(f"Orig verts: {orig_vert_count}, Mirror-only verts: {new_vert_count}")

new_basis = np.zeros(new_vert_count * 3, dtype=np.float32)
new_mesh.vertices.foreach_get("co", new_basis)
new_basis = new_basis.reshape(-1, 3)

half = new_vert_count // 2
print(f"Half: {half}")

# 3. Clear shape keys and remove mirror modifier only
obj.shape_key_clear()
for mod in list(obj.modifiers):
    if mod.type == 'MIRROR':
        obj.modifiers.remove(mod)

# Re-enable subdiv
for mod in obj.modifiers:
    if mod.type == 'SUBSURF':
        mod.show_viewport = True

# 4. Swap mesh
old_mesh = obj.data
obj.data = new_mesh
bpy.data.meshes.remove(old_mesh)

# Re-grab object
obj = bpy.data.objects["Eyes"]

# 5. Add basis
basis_sk = obj.shape_key_add(name=key_names[0], from_mix=False)
basis_sk.data.foreach_set("co", new_basis.flatten().astype(np.float32))

# 6. Rebuild each shape key - clean 50/50 split now
for i in range(1, len(key_names)):
    delta = all_coords[i] - basis_orig  # (orig_vert_count, 3)
    delta_mirror = delta.copy()
    delta_mirror[:, 0] *= -1

    new_coords = new_basis.copy()

    # First half = left eye, same delta
    for v in range(half):
        orig_v = min(v * orig_vert_count // half, orig_vert_count - 1)
        new_coords[v] += delta[orig_v]

    # Second half = right eye, mirrored delta
    for v in range(half, new_vert_count):
        orig_v = min((v - half) * orig_vert_count // half, orig_vert_count - 1)
        new_coords[v] += delta_mirror[orig_v]

    sk = obj.shape_key_add(name=key_names[i], from_mix=False)
    sk.value = key_values[i]
    sk.slider_min = key_mins[i]
    sk.slider_max = key_maxs[i]
    sk.data.foreach_set("co", new_coords.flatten().astype(np.float32))

obj.data.update()
print(f"Done! Verts: {new_vert_count}, Shape keys: {[kb.name for kb in obj.data.shape_keys.key_blocks]}")
