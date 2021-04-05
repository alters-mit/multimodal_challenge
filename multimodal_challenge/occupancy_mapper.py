from typing import List, Tuple
from pathlib import Path
import numpy as np
from tdw.floorplan_controller import FloorplanController
from tdw.output_data import Raycast, Images
from tdw.tdw_utils import TDWUtils
from magnebot.scene_environment import SceneEnvironment
from magnebot.constants import OCCUPANCY_CELL_SIZE
from magnebot.util import get_data
from multimodal_challenge.paths import OCCUPANCY_MAPS_DIRECTORY
from multimodal_challenge.util import get_object_init_commands


class OccupancyMapper(FloorplanController):
    """
    Create an occupancy map and image of a scene.

    This is used by [`init_data.py`](../dataset/init_data.md).
    """

    def __init__(self, port: int = 1071):
        """
        :param port: The socket port.
        """

        super().__init__(port=port, check_version=True, launch_build=True)

    def create(self, scene: str, layout: int, image_dir: Path) -> None:
        """
        Create the following for a scene_layout:

        - An occupancy map (which will be stored in this module)
        - An image of the scene (stored in the documentation folder of the repo)

        :param scene: The name of the scene.
        :param layout: The layout index.
        :param image_dir: The output directory for the image.
        """

        screen_width: int = 1280
        screen_height: int = 720

        occupancy_map = list()
        commands = self.get_scene_init_commands(scene=scene, layout=layout, audio=True)
        # Hide the roof and remove any existing position markers.
        commands.extend([{"$type": "set_floorplan_roof",
                          "show": False},
                         {"$type": "simulate_physics",
                          "value": True},
                         {"$type": "send_environments"},
                         {"$type": "set_img_pass_encoding",
                          "value": False},
                         {"$type": "set_render_quality",
                          "render_quality": 5},
                         {"$type": "set_screen_size",
                          "width": screen_width,
                          "height": screen_height}])
        commands.extend(TDWUtils.create_avatar(position={"x": 0, "y": 20, "z": 0},
                                               look_at=TDWUtils.VECTOR3_ZERO))
        commands.extend([{"$type": "set_pass_masks",
                          "pass_masks": ["_img"]},
                         {"$type": "send_images"}])
        # Send the commands.
        resp = self.communicate(commands)
        # Save the image.
        images = get_data(resp=resp, d_type=Images)
        TDWUtils.save_images(images=images, filename=f"{scene}_{layout}",
                             output_directory=str(image_dir.joinpath("scene_layouts").resolve()),
                             append_pass=False)
        scene_env = SceneEnvironment(resp=resp)
        # Spherecast to each point.
        x = scene_env.x_min
        while x < scene_env.x_max:
            z = scene_env.z_min
            pos_row: List[int] = list()
            while z < scene_env.z_max:
                origin = {"x": x, "y": 4, "z": z}
                destination = {"x": x, "y": -1, "z": z}
                # Spherecast at the "cell".
                resp = self.communicate({"$type": "send_spherecast",
                                         "origin": origin,
                                         "destination": destination,
                                         "radius": OCCUPANCY_CELL_SIZE / 2})
                # Get the y values of each position in the spherecast.
                ys = []
                hits = []
                hit_objs = []
                for j in range(len(resp) - 1):
                    raycast = Raycast(resp[j])
                    raycast_y = raycast.get_point()[1]
                    is_hit = raycast.get_hit() and (not raycast.get_hit_object() or raycast_y > 0.01)
                    if is_hit:
                        ys.append(raycast_y)
                        hit_objs.append(raycast.get_hit_object())
                    hits.append(is_hit)
                # This position is outside the environment.
                if len(ys) == 0 or len(hits) == 0 or len([h for h in hits if h]) == 0 or max(ys) > 2.8:
                    occupied = -1
                else:
                    # This space is occupied if:
                    # 1. The spherecast hit any objects.
                    # 2. The surface is higher than floor level.
                    if any(hit_objs) and max(ys) > 0.03:
                        occupied = 1
                    # The position is free.
                    else:
                        occupied = 0
                pos_row.append(occupied)
                z += OCCUPANCY_CELL_SIZE
            occupancy_map.append(pos_row)
            x += OCCUPANCY_CELL_SIZE
        occupancy_map = np.array(occupancy_map)
        # Sort the free positions of the occupancy map into continuous "islands".
        # Then, sort that list of lists by length.
        # The longest list is the biggest "island" i.e. the navigable area.
        non_navigable = list(sorted(OccupancyMapper._get_islands(occupancy_map=occupancy_map), key=len))[:-1]
        # Record non-navigable positions.
        for island in non_navigable:
            for p in island:
                occupancy_map[p[0]][p[1]] = 2
        # Save the occupancy map.
        np.save(str(OCCUPANCY_MAPS_DIRECTORY.joinpath(f"{scene}_{layout}").resolve()), occupancy_map)

        self.communicate({"$type": "terminate"})
        self.socket.close()

    def get_scene_init_commands(self, scene: str, layout: int, audio: bool) -> List[dict]:
        commands = [self.get_add_scene(scene_name=scene),
                    {"$type": "set_aperture",
                     "aperture": 8.0},
                    {"$type": "set_focus_distance",
                     "focus_distance": 2.25},
                    {"$type": "set_post_exposure",
                     "post_exposure": 0.4},
                    {"$type": "set_ambient_occlusion_intensity",
                     "intensity": 0.175},
                    {"$type": "set_ambient_occlusion_thickness_modifier",
                     "thickness": 3.5},
                    {"$type": "set_shadow_strength",
                     "strength": 1.0}]
        commands.extend(get_object_init_commands(scene=scene, layout=layout))
        return commands

    @staticmethod
    def _get_islands(occupancy_map: np.array) -> List[List[Tuple[int, int]]]:
        """
        :param occupancy_map: The occupancy map.

        :return: A list of all islands, i.e. continuous zones of traversability on the occupancy map.
        """

        # Positions that have been reviewed so far.
        traversed: List[Tuple[int, int]] = []
        islands: List[List[Tuple[int, int]]] = list()

        for ox, oy in np.ndindex(occupancy_map.shape):
            p = (ox, oy)
            if p in traversed:
                continue
            island = OccupancyMapper._get_island(occupancy_map=occupancy_map, p=p)
            if len(island) > 0:
                for island_position in island:
                    traversed.append(island_position)
                islands.append(island)
        return islands

    @staticmethod
    def _get_island(occupancy_map: np.array, p: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        Fill the island (a continuous zone) that position `p` belongs to.

        :param occupancy_map: The occupancy map.
        :param p: The position.

        :return: An island of positions as a list of (x, z) tuples.
        """

        to_check = [p]
        island: List[Tuple[int, int]] = list()
        while len(to_check) > 0:
            # Check the next position.
            p = to_check.pop(0)
            if p[0] < 0 or p[0] >= occupancy_map.shape[0] or p[1] < 0 or p[1] >= occupancy_map.shape[1] or \
                    occupancy_map[p[0]][p[1]] != 0 or p in island:
                continue
            # Mark the position as traversed.
            island.append(p)
            # Check these neighbors.
            px, py = p
            to_check.extend([(px, py + 1),
                             (px + 1, py + 1),
                             (px + 1, py),
                             (px + 1, py - 1),
                             (px, py - 1),
                             (px - 1, py - 1),
                             (px - 1, py),
                             (px - 1, py + 1)])
        return island
