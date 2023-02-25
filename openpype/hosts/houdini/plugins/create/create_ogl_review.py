# -*- coding: utf-8 -*-
"""Creator plugin for creating opengl reviews."""
from openpype.hosts.houdini.api import plugin
from openpype.pipeline import CreatedInstance


class CreateOGLReview(plugin.HoudiniCreator):
    """Open GL Review"""

    identifier = "io.openpype.creators.houdini.oglreview"
    label = "OGL Review"
    family = "review"
    icon = "video-camera"

    # Default settings for the ROP
    # todo: expose in OpenPype settings?
    override_resolution = False
    width = 1280
    height = 720
    aspect = 1.0
    ext = ".exr"
    file_padding = "$4F"
    filepath = f'$HIP/review/`chs("subset")`/`chs("subset")`.{file_padding}.{ext}'

    def create(self, subset_name, instance_data, pre_create_data):
        import hou

        instance_data.pop("active", None)

        instance_data.update({"node_type": "opengl"})

        instance = super(CreateOGLReview, self).create(
            subset_name,
            instance_data,
            pre_create_data)  # type: CreatedInstance

        instance_node = hou.node(instance.get("instance_node"))

        frame_range = hou.playbar.frameRange()

        parms = {
            "picture": self.filepath,
            # Render frame range
            "trange": 1,

            # Unlike many other ROP nodes the opengl node does not default
            # to expression of $FSTART and $FEND so we preserve that behavior
            # but do set the range to the frame range of the playbar
            "f1": frame_range[0],
            "f2": frame_range[1],
        }

        if self.override_resolution:
            # Override resolution
            parms.update({
                "tres": True,   # Override Camera Resolution
                "res1": self.width,
                "res2": self.height,
                "aspect": self.aspect
            })

        if self.selected_nodes:
            # todo: allow only object paths?
            node_paths = " ".join(node.path() for node in self.selected_nodes)
            parms.update({"scenepath": node_paths})

        instance_node.setParms(parms)

        # Lock any parameters in this list
        to_lock = [
            "family",
            "id"
        ]
        self.lock_parameters(instance_node, to_lock)
