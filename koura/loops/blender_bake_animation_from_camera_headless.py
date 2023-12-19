import bpy
import os
from datetime import datetime
import sys
import bpy


def print(data):
    sys.stdout.write(str(data) + "\n")
    for window in bpy.context.window_manager.windows:
        screen = window.screen
        for area in screen.areas:
            if area.type == "CONSOLE":
                override = {"window": window, "screen": screen, "area": area}
                bpy.ops.console.scrollback_append(
                    override, text=str(data), type="OUTPUT"
                )


render_collection_name = "Gen"
reprojection_collection_name = "Reprojection"


def execute():
    scene = bpy.context.scene

    # obj = bpy.data.objects[object_name]
    render_collection = bpy.data.collections[render_collection_name]
    reprojection_collection = bpy.data.collections[reprojection_collection_name]

    reprojection_collection.hide_render = True

    image_name = render_collection_name + "_BakedTexture"
    img = bpy.data.images.new(image_name, 3840, 2160, alpha=True)

    # Set the frame range and frame step
    start_frame = scene.frame_start
    end_frame = scene.frame_end
    frame_step = 1

    filepath = bpy.data.filepath
    directory = os.path.dirname(filepath)

    now = datetime.now()
    now_str = now.strftime("%d-%m-%Y %H-%M-%S")

    relative_folder = f"outputs/{now_str}"
    folder = f"{directory}/{relative_folder}"
    if not os.path.exists(folder):
        os.makedirs(folder)

    print(f"Baking files to {folder}")

    BAKE_NODE_NAME = "Bake_node"
    RENDER_TEXTURE_NAME = "Render Result"
    RENDER_TEXTURE_NODE_NAME = "Image Texture"
    BAKE_TYPE = "COMBINED"
    # BAKE_PASS_FILTER = {"DIRECT", "INDIRECT"}

    # Due to the presence of any multiple materials, it seems necessary to iterate on all the materials, and assign them a node + the image to bake.
    for obj in reprojection_collection.objects:
        mat = obj.active_material
        mat.use_nodes = True  # Here it is assumed that the materials have been created with nodes, otherwise it would not be possible to assign a node for the Bake, so this step is a bit useless
        nodes = mat.node_tree.nodes
        texture_node = nodes.new("ShaderNodeTexImage")
        texture_node.name = BAKE_NODE_NAME
        texture_node.select = True
        nodes.active = texture_node
        texture_node.image = img  # Assign the image to the node

    # Loop through each frame
    for frame in range(start_frame, end_frame + 1, frame_step):
        # Set the current frame
        scene.frame_current = frame

        render_collection.hide_render = False
        # Set the render file location
        render_filepath = f"{folder}/render_{frame}.png"
        scene.render.filepath = render_filepath

        # Render the image
        bpy.ops.render.render(write_still=True)
        render_collection.hide_render = True

        rendered_image = bpy.data.images[RENDER_TEXTURE_NAME]

        for obj in reprojection_collection.objects:
            mat = obj.active_material
            nodes = mat.node_tree.nodes
            texture_node = nodes[RENDER_TEXTURE_NODE_NAME]
            texture_node.image = bpy.data.images.load(render_filepath)
            nodes.active = nodes[BAKE_NODE_NAME]

        bpy.context.view_layer.objects.active = obj
        reprojection_collection.hide_render = False
        bpy.ops.object.bake(
            type=BAKE_TYPE,
            save_mode="EXTERNAL",
            use_selected_to_active=False,
            # pass_filter=BAKE_PASS_FILTER,
        )
        reprojection_collection.hide_render = True

        # Save the baked image
        path = f"{folder}/{obj.name}_{frame:04}.png"
        img.save_render(path)

        print(f"Baked {frame}/{end_frame-start_frame}")

    # In the last step, we are going to delete the nodes we created earlier
    for mat in obj.data.materials:
        for n in mat.node_tree.nodes:
            if n.name == "Bake_node":
                mat.node_tree.nodes.remove(n)

    print("Baking completed!")

    return {"FINISHED"}


if __name__ == "__main__":
    execute()
