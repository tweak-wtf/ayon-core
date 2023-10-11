import os
import contextlib
import pyblish.api
from pymxs import runtime as rt
from openpype.pipeline import publish
from openpype.hosts.max.api.lib import (
    viewport_camera,
    get_max_version,
    set_preview_arg
)


class ExtractReviewAnimation(publish.Extractor):
    """
    Extract Review by Review Animation
    """

    order = pyblish.api.ExtractorOrder + 0.001
    label = "Extract Review Animation"
    hosts = ["max"]
    families = ["review"]

    def process(self, instance):
        staging_dir = self.staging_dir(instance)
        ext = instance.data.get("imageFormat")
        filename = "{0}..{1}".format(instance.name, ext)
        start = int(instance.data["frameStart"])
        end = int(instance.data["frameEnd"])
        fps = float(instance.data["fps"])
        filepath = os.path.join(staging_dir, filename)
        filepath = filepath.replace("\\", "/")
        filenames = self.get_files(
            instance.name, start, end, ext)

        self.log.debug(
            "Writing Review Animation to"
            " '%s' to '%s'" % (filename, staging_dir))

        review_camera = instance.data["review_camera"]
        if get_max_version() >= 2024:
            with viewport_camera(review_camera):
                preview_arg = set_preview_arg(
                    instance, filepath, start, end, fps)
                rt.execute(preview_arg)
        else:
            visual_style_preset = instance.data.get("visualStyleMode")
            nitrousGraphicMgr = rt.NitrousGraphicsManager
            viewport_setting = nitrousGraphicMgr.GetActiveViewportSetting()
            with viewport_camera(review_camera) and (
                self._visual_style_option(
                    viewport_setting, visual_style_preset)
            ):
                viewport_setting.VisualStyleMode = rt.Name(
                    visual_style_preset)
                preview_arg = set_preview_arg(
                    instance, filepath, start, end, fps)
                rt.execute(preview_arg)

        tags = ["review"]
        if not instance.data.get("keepImages"):
            tags.append("delete")

        self.log.debug("Performing Extraction ...")

        representation = {
            "name": instance.data["imageFormat"],
            "ext": instance.data["imageFormat"],
            "files": filenames,
            "stagingDir": staging_dir,
            "frameStart": instance.data["frameStart"],
            "frameEnd": instance.data["frameEnd"],
            "tags": tags,
            "preview": True,
            "camera_name": review_camera
        }
        self.log.debug(f"{representation}")

        if "representations" not in instance.data:
            instance.data["representations"] = []
        instance.data["representations"].append(representation)

    def get_files(self, filename, start, end, ext):
        file_list = []
        for frame in range(int(start), int(end) + 1):
            actual_name = "{}.{:04}.{}".format(
                filename, frame, ext)
            file_list.append(actual_name)

        return file_list

    @contextlib.contextmanager
    def _visual_style_option(self, viewport_setting, visual_style):
        """Function to set visual style options

        Args:
            visual_style (str): visual style for active viewport

        Returns:
            list: the argument which can set visual style
        """
        current_setting = viewport_setting.VisualStyleMode
        if visual_style != current_setting:
            try:
                viewport_setting.VisualStyleMode = rt.Name(
                    visual_style)
                yield
            finally:
                viewport_setting.VisualStyleMode = current_setting
