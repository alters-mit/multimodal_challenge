from json import loads
import numpy as np
from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from multimodal_challenge.paths import REHEARSAL_DIRECTORY
from multimodal_challenge.util import get_drop_zones, get_object_init_commands


class DropZoneAnalyzer(Controller):
    """
    This is a backend tool meant for analyzing the average rate at which objects fall into DropZones.
    You can run this after running `rehearsal.py`. You don't need to run this to run `dataset.py`.
    """

    """:class_var
    Lerp the position marker colors from this color.
    """
    COLOR_A: np.array = np.array([0, 0, 1, 1])
    """:class_var
    Lerp the position marker colors to this color.
    """
    COLOR_B: np.array = np.array([1, 0, 0, 1])

    def run(self, scene: str, layout: int) -> None:
        """
        Every time `rehearsal.py` records `Drop` data, it also records the index of the `DropZone` the object landed in.
        This function loads that list of indices, converts them to `add_position_marker` commands, and colorizes them.
        Red circles have the most drops and blue circles have the least.

        :param scene: The name of the scene.
        :param layout: The layout index.
        """

        drop_zones = get_drop_zones(f"{scene}_{layout}.json")
        indices = loads(REHEARSAL_DIRECTORY.joinpath(f"{scene}_{layout}_drop_zones.json").read_text(encoding="utf-8"))
        max_instances = 0
        for i in range(len(indices)):
            if indices.count(indices[i]) > max_instances:
                max_instances = indices.count(indices[i])
        commands = [self.get_add_scene(scene_name=scene),
                    {"$type": "set_floorplan_roof",
                     "show": False}]
        print("Max instances:", max_instances)
        for i, drop_zone in enumerate(drop_zones):
            # Lerp between the two colors to show how close the value of this drop zone
            # compared to the drop zone with the most drops.
            t = indices.count(i) / max_instances
            color = DropZoneAnalyzer.COLOR_A + (DropZoneAnalyzer.COLOR_B - DropZoneAnalyzer.COLOR_A) * t
            print(i, indices.count(i) / len(indices))
            commands.append({"$type": "add_position_marker",
                             "position": TDWUtils.array_to_vector3(drop_zone.center),
                             "shape": "circle",
                             "scale": drop_zone.radius,
                             "color": TDWUtils.array_to_color(color)})
        commands.extend(get_object_init_commands(scene=scene, layout=layout))
        self.communicate(commands)


if __name__ == "__main__":
    c = DropZoneAnalyzer(launch_build=False)
    c.run("mm_kitchen_1_a", 0)
