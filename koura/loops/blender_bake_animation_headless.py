import bpy
import os
from datetime import datetime
import sys


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


object_name = "stage"


def execute():
    scene = bpy.context.scene
    obj = bpy.data.objects[object_name]

    image_name = obj.name + "_BakedTexture"
    img = bpy.data.images.new(image_name, 3840, 2160)

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

    bpy.context.view_layer.objects.active = obj

    # Due to the presence of any multiple materials, it seems necessary to iterate on all the materials, and assign them a node + the image to bake.
    for mat in obj.data.materials:
        mat.use_nodes = True  # Here it is assumed that the materials have been created with nodes, otherwise it would not be possible to assign a node for the Bake, so this step is a bit useless
        nodes = mat.node_tree.nodes
        texture_node = nodes.new("ShaderNodeTexImage")
        texture_node.name = "Bake_node"
        texture_node.select = True
        nodes.active = texture_node
        texture_node.image = img  # Assign the image to the node

    # Loop through each frame
    for frame in range(start_frame, end_frame + 1, frame_step):
        # Set the current frame
        scene.frame_current = frame

        # Bake the frame
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.bake(
            type="COMBINED", save_mode="EXTERNAL", use_selected_to_active=False
        )

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
