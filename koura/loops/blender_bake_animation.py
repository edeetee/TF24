import bpy
import os
from datetime import datetime

def print(data):
    for window in bpy.context.window_manager.windows:
        screen = window.screen
        for area in screen.areas:
            if area.type == 'CONSOLE':
                override = {'window': window, 'screen': screen, 'area': area}
                bpy.ops.console.scrollback_append(override, text=str(data), type="OUTPUT")

class BakeAnimationPanel(bpy.types.Panel):
    """Custom panel for baking animation using Eevee"""
    bl_idname = "OBJECT_PT_bake_animation"
    bl_label = "Bake Animation"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    def draw(self, context):
        layout = self.layout
        obj = context.object

        # Check if object is valid
        if not obj or obj.type not in {'MESH', 'CURVE'}:
            return

        # Add controls
        layout.prop(obj, "use_eevee_bake", text="Use Eevee")
        row = layout.row()
        row.prop(context.scene, "frame_start", text="Start Frame")
        row.prop(context.scene, "frame_end", text="End Frame")
        layout.prop(context.scene, "render.filepath", text="Output Directory")

        # Progress bar
        progress_bar = layout.prop(context.scene, "bake_progress", text="Progress")

        # Bake button
        layout.operator("bake_animation.operator", text="Bake")

class BakeAnimationOperator(bpy.types.Operator):
    """Operator for baking animation using Eevee with UI update"""
    bl_idname = "bake_animation.operator"
    bl_label = "Bake Animation"

    def execute(self, context):
        scene = bpy.context.scene
        obj = bpy.context.active_object
        
        image_name = obj.name + '_BakedTexture'
        img = bpy.data.images.new(image_name,3840,2160)

        # Set the frame range and frame step
        start_frame = scene.frame_start
        end_frame = scene.frame_end
        frame_step = 1
        
        filepath = bpy.data.filepath
        directory = os.path.dirname(filepath)
        
        now = datetime.now()
        now_str = now.strftime("%d-%m-%Y %H-%M-%S")
        
        relative_folder=f"outputs/{now_str}"
        folder = f"{directory}/{relative_folder}"
        if not os.path.exists(folder):
            os.makedirs(folder)
        print(f"saving files to {folder}")
        
        #Due to the presence of any multiple materials, it seems necessary to iterate on all the materials, and assign them a node + the image to bake.
        for mat in obj.data.materials:
            mat.use_nodes = True #Here it is assumed that the materials have been created with nodes, otherwise it would not be possible to assign a node for the Bake, so this step is a bit useless
            nodes = mat.node_tree.nodes
            texture_node = nodes.new('ShaderNodeTexImage')
            texture_node.name = 'Bake_node'
            texture_node.select = True
            nodes.active = texture_node
            texture_node.image = img #Assign the image to the node
        
        
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

        # Loop through each frame
        for frame in range(start_frame, end_frame + 1, frame_step):
            # Set the current frame
            scene.frame_current = frame
            
            scene.bake_progress = frame
            
            # Bake the frame
#            bpy.ops.render.render(write_still=True, animation=False)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.bake(type='COMBINED', save_mode="EXTERNAL", use_selected_to_active=False)

            # Save the baked image
#            baked_image = bpy.data.images['Render Result']
            path = f"{folder}/{obj.name}_{frame:04}.png"
            img.save_render(path)
            
            # Update UI after each frame
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)

        scene.bake_progress = 0
        
        #In the last step, we are going to delete the nodes we created earlier
        for mat in obj.data.materials:
            for n in mat.node_tree.nodes:
                if n.name == 'Bake_node':
                    mat.node_tree.nodes.remove(n)

        print("Baking completed!")

        return {'FINISHED'}

# Register custom properties
def register():
    bpy.utils.register_class(BakeAnimationPanel)
    bpy.utils.register_class(BakeAnimationOperator)
    bpy.types.Scene.bake_progress = bpy.props.FloatProperty(name="Bake Progress", default=0.0)

# Unregister custom properties
def unregister():
    bpy.utils.unregister_class(BakeAnimationPanel)
    bpy.utils.unregister_class(BakeAnimationOperator)
    del bpy.types.Scene.bake_progress

if __name__ == "__main__":
    register()
