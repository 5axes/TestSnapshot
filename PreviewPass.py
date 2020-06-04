# Original source by Ultimaker, modified
# https://github.com/Ultimaker/Cura/blob/master/cura/PreviewPass.py

# Copyright (c) 2018 Ultimaker B.V.
# Cura is released under the terms of the LGPLv3 or higher.

from typing import Optional, TYPE_CHECKING, cast


from cura.CuraApplication import CuraApplication
from UM.Resources import Resources

from UM.Logger import Logger
from UM.View.RenderPass import RenderPass
from UM.View.GL.OpenGL import OpenGL
from UM.View.RenderBatch import RenderBatch


from UM.Scene.Iterator.DepthFirstIterator import DepthFirstIterator
from cura.Scene.CuraSceneNode import CuraSceneNode

if TYPE_CHECKING:
    from UM.View.GL.ShaderProgram import ShaderProgram
    from UM.Scene.Camera import Camera





# Make color brighter by normalizing it (maximum factor 2.5 brighter)
# color_list is a list of 4 elements: [r, g, b, a], each element is a float 0..1
def prettier_color(color_list):
    maximum = max(color_list[:3])
    if maximum > 0:
        factor = min(1 / maximum, 2.5)
    else:
        factor = 1.0
    return [min(i * factor, 1.0) for i in color_list]


##  A render pass subclass that renders slicable objects with default parameters.
#   It uses the active camera by default, but it can be overridden to use a different camera.
#
#   This is useful to get a preview image of a scene taken from a different location as the active camera.
class PreviewPass(RenderPass):
    def __init__(self, width: int, height: int) -> None:
        super().__init__("preview", width, height, 0)

        self._camera = None  # type: Optional[Camera]

        self._renderer = CuraApplication.getInstance().getRenderer()

        self._shader = None  # type: Optional[ShaderProgram]
        self._non_printing_shader = None  # type: Optional[ShaderProgram]
        self._support_mesh_shader = None  # type: Optional[ShaderProgram]

        self._scene = CuraApplication.getInstance().getController().getScene()

        #self._platform_shader = None
        #self._platform_texture = None

    #   Set the camera to be used by this render pass
    #   if it's None, the active camera is used
    def setCamera(self, camera: Optional["Camera"]):
        self._camera = camera

    def render(self) -> None:

        if not self._shader:
            self._shader = OpenGL.getInstance().createShaderProgram(Resources.getPath(Resources.Shaders, "overhang.shader"))
            if self._shader:
                self._shader.setUniformValue("u_overhangAngle", 1.0)
                self._shader.setUniformValue("u_ambientColor", [0.1, 0.1, 0.1, 1.0])
                self._shader.setUniformValue("u_specularColor", [0.6, 0.6, 0.6, 1.0])
                self._shader.setUniformValue("u_shininess", 20.0)
                self._shader.setUniformValue("u_renderError", 0.0)  # We don't want any error markers!.
                self._shader.setUniformValue("u_faceId", -1)  # Don't render any selected faces in the preview.

        if not self._non_printing_shader:
            if self._non_printing_shader:
                self._non_printing_shader = OpenGL.getInstance().createShaderProgram(Resources.getPath(Resources.Shaders, "transparent_object.shader"))
                self._non_printing_shader.setUniformValue("u_diffuseColor", [0.5, 0.5, 0.5, 0.5])
                self._non_printing_shader.setUniformValue("u_opacity", 0.6)

        if not self._support_mesh_shader:
            self._support_mesh_shader = OpenGL.getInstance().createShaderProgram(Resources.getPath(Resources.Shaders, "striped.shader"))
            if self._support_mesh_shader:
                self._support_mesh_shader.setUniformValue("u_vertical_stripes", True)
                self._support_mesh_shader.setUniformValue("u_width", 5.0)

        #if not self._platform_shader:

        #    self._platform_shader = OpenGL.getInstance().createShaderProgram(Resources.getPath(Resources.Shaders, "platform.shader"))
        #    self._platform_texture = OpenGL.getInstance().createTexture()

        #    if self._platform_shader:
        #        global_container_stack = CuraApplication.getInstance().getGlobalContainerStack()
        #        if global_container_stack:
        #            container = global_container_stack.findContainer({ "platform_texture": "*" })
        #            if container:
        #                texture_file = container.getMetaDataEntry("platform_texture")
        #                try:
        #                    Logger.log("d", "rlh: loading %s", texture_file)
        #                    self._platform_texture.load(Resources.getPath(Resources.Images, texture_file))
        #                except FileNotFoundError:
        #                    Logger.log("w", "Unable to find platform texture [%s] as specified in the definition", texture_file)

        #    #self._platform_shader.setTexture(0, self._platform_texture)

        self._gl.glClearColor(0.0, 0.0, 0.0, 0.0)
        self._gl.glClear(self._gl.GL_COLOR_BUFFER_BIT | self._gl.GL_DEPTH_BUFFER_BIT)

        # Create batches to be rendered
        batch = RenderBatch(self._shader)
        batch_support_mesh = RenderBatch(self._support_mesh_shader)
        #batch_platform = RenderBatch(self._platform_shader)

        from cura.Scene.ConvexHullNode import ConvexHullNode
        from UM.Scene.Platform import Platform

        # Fill up the batch with objects that can be sliced.
        for node in DepthFirstIterator(self._scene.getRoot()):

            if type(node) is CuraSceneNode:
                if hasattr(node, "_outside_buildarea") and not getattr(node, "_outside_buildarea"):
                    if node.callDecoration("isSliceable") and node.getMeshData() and node.isVisible():
                        per_mesh_stack = node.callDecoration("getStack")
                        if node.callDecoration("isNonThumbnailVisibleMesh"):
                            # Non printing mesh
                            continue
                        elif per_mesh_stack is not None and per_mesh_stack.getProperty("support_mesh", "value"):
                            # Support mesh
                            uniforms = {}
                            shade_factor = 0.6
                            diffuse_color = cast(CuraSceneNode, node).getDiffuseColor()
                            diffuse_color2 = [
                                diffuse_color[0] * shade_factor,
                                diffuse_color[1] * shade_factor,
                                diffuse_color[2] * shade_factor,
                                1.0]
                            uniforms["diffuse_color"] = prettier_color(diffuse_color)
                            uniforms["diffuse_color_2"] = diffuse_color2
                            batch_support_mesh.addItem(node.getWorldTransformation(), node.getMeshData(), uniforms = uniforms)
                        else:
                            # Normal scene node
                            uniforms = {}
                            uniforms["diffuse_color"] = prettier_color(cast(CuraSceneNode, node).getDiffuseColor())
                            batch.addItem(node.getWorldTransformation(), node.getMeshData(), uniforms = uniforms)
                continue

            #if type(node) is ConvexHullNode:
            #    continue

            #if type(node) is Platform:
            #    uniforms = {}
            #    batch_platform.addItem(node.getWorldTransformation(), node.getMeshData(), uniforms = uniforms)
            #    continue

        self.bind()

        if self._camera is None:
            render_camera = CuraApplication.getInstance().getController().getScene().getActiveCamera()
        else:
            render_camera = self._camera

        batch.render(render_camera)
        batch_support_mesh.render(render_camera)
        #batch_platform.render(render_camera)

        self.release()
