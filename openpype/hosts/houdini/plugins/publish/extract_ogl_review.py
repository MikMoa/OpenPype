import os
import pyblish.api
from pprint import pformat

from openpype.pipeline import publish
from openpype.hosts.houdini.api.lib import render_rop, splitext

import hou


class ExtractOGLReview(publish.Extractor):

    order = pyblish.api.ExtractorOrder
    label = "Extract OGL Review"
    families = ["review"]
    hosts = ["houdini"]
    optional = True

    def process(self, instance):

        ropnode = hou.node(instance.data["instance_node"])

        # Get the filename from the copoutput parameter
        # `.evalParm(parameter)` will make sure all tokens are resolved
        output = ropnode.evalParm("picture")
        staging_dir = os.path.dirname(output)
        instance.data["stagingDir"] = staging_dir
        file_name = os.path.basename(output)

        self.log.info("Writing review '%s' to '%s'" % (file_name, staging_dir))

        render_rop(ropnode)

        # Unfortunately user interrupting the extraction does not raise an
        # error and thus still continues to the integrator. To capture that
        # we make sure all files exist
        files = instance.data["frames"]
        missing = [fname for fname in files
                   if not os.path.exists(os.path.join(staging_dir, fname))]
        if missing:
            raise RuntimeError("Failed to complete review extraction. "
                               "Missing output files: {}".format(missing))

        _, ext = splitext(files[0], [])
        ext = ext.lstrip(".")

        if "representations" not in instance.data:
            instance.data["representations"] = []

        tags = ["review"]
        instance.data["families"] = ['ftrack']

        representation = {
            "name": ext,
            "ext": ext,
            "files": files,
            "stagingDir": staging_dir,
            "frameStart": instance.data["frameStart"],
            "frameEnd": instance.data["frameEnd"],
            "tags" : tags
        }


        self.log.info(pformat(representation))
        instance.data["representations"].append(representation)
