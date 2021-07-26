from typing import List
import numpy as np
from tdw.controller import Controller
from tdw.librarian import SceneLibrarian
from tdw.output_data import OutputData, Overlap
from magnebot.constants import OCCUPANCY_CELL_SIZE
from multimodal_challenge.util import get_object_init_commands
from multimodal_challenge.paths import OCCUPANCY_MAPS_DIRECTORY, MAGNEBOT_OCCUPANCY_MAPS_DIRECTORY
from multimodal_challenge.dataset.constants import MIN_OBJECT_DISTANCE_FROM_MAGNEBOT
from multimodal_challenge.dataset.add_ons.occupancy_map import OccupancyMap


class OccupancyMapper(Controller):
    """
    For each scene_layout combination, create occupancy maps for object placement and for spawning the Magnebot.
    Verify that there are enough valid places for the Magnebot and objects.
    """

    def __init__(self, port: int = 1071):
        super().__init__(port=port, launch_build=False)
        self.scene_librarian: SceneLibrarian = SceneLibrarian()

    def create(self, scene: str, layout: int) -> None:
        """
        Create occupancy maps for a scene_layout combination.

        :param scene: The scene name.
        :param layout: The layout index.
        """

        # Load the scene and generate the occupancy map.
        o: OccupancyMap = OccupancyMap(cell_size=OCCUPANCY_CELL_SIZE)
        scene_record = self.scene_librarian.get_record(scene)
        commands: List[dict] = [{"$type": "add_scene",
                                 "name": scene_record.name,
                                 "url": scene_record.get_url()},
                                {"$type": "destroy_all_objects"}]
        commands.extend(get_object_init_commands(scene=scene, layout=layout))
        commands.extend(o.get_initialization_commands())
        o.initialized = True
        resp = self.communicate(commands)
        o.on_send(resp=resp)
        o.generate()
        resp = self.communicate(o.commands)
        o.on_send(resp=resp)

        # We want the Magnebot to have enough space to freely turn at the start of a trial.
        # Get overlap shapes at each free position that are somewhat bigger than the cells.
        capsule_half_height = (o.scene_bounds.y_max - o.scene_bounds.y_min) / 2
        magnebot_cell_size = OCCUPANCY_CELL_SIZE * 1.25
        magnebot_occupancy_map: np.array = np.ones(shape=o.occupancy_map.shape, dtype=int)
        commands: List[dict] = list()
        for idx, idz in np.ndindex(o.occupancy_map.shape):
            if o.occupancy_map[idx][idz] == 0:
                x, z = o.get_occupancy_position(idx, idz)
                cast_id = idx + (idz * 10000)
                commands.append({"$type": "send_overlap_capsule",
                                 "end": {"x": x, "y": capsule_half_height, "z": z},
                                 "radius": magnebot_cell_size,
                                 "position": {"x": x, "y": -capsule_half_height, "z": z},
                                 "id": cast_id})
        # Generate the Magnebot occupancy map.
        resp = self.communicate(commands)
        for i in range(len(resp) - 1):
            r_id = OutputData.get_data_type_id(resp[i])
            if r_id == "over":
                overlap = Overlap(resp[i])
                # There are no objects here.
                if not overlap.get_walls() and overlap.get_env() and len(overlap.get_object_ids()) == 0:
                    cast_id = overlap.get_id()
                    idx = cast_id % 10000
                    idz = int((cast_id - (cast_id % 10000)) / 10000)
                    magnebot_occupancy_map[idx][idz] = 0
        # Make sure that there are positions to place objects.
        # There must be at least 1 place to drop an object that is far away from each Magnebot spawn position.
        for idxm, idzm in np.ndindex(magnebot_occupancy_map.shape):
            if magnebot_occupancy_map[idxm][idzm] != 0:
                continue
            xm, zm = o.get_occupancy_position(idxm, idzm)
            pm = np.array([xm, zm])
            has_object_spawns: bool = False
            for idxo, idzo in np.ndindex(o.occupancy_map.shape):
                if idxo == idxm and idzo == idzm:
                    continue
                if o.occupancy_map[idxo][idzo] != 0:
                    continue
                xo, zo = o.get_occupancy_position(idxo, idzo)
                if np.linalg.norm(pm - np.array([xo, zo])) >= MIN_OBJECT_DISTANCE_FROM_MAGNEBOT:
                    has_object_spawns = True
                    break
            # If there aren't any sufficiently distance object spawn positions from this Magnebot spawn position,
            # this isn't a valid Magnebot spawn position.
            if not has_object_spawns:
                magnebot_occupancy_map[idxm][idzm] = 1
        # Check if there are any Magnebot spawn positions.
        has_magnebot_positions = False
        for idxm, idzm in np.ndindex(magnebot_occupancy_map.shape):
            if magnebot_occupancy_map[idxm][idzm] == 0:
                has_magnebot_positions = True
                break
        filename = f"{scene}_{layout}"
        if not has_magnebot_positions:
            o.show()
            o.commands.extend([{"$type": "set_floorplan_roof",
                                "show": False},
                               {"$type": "pause_editor"}])
            self.communicate(o.commands)
            raise Exception(filename)
        # Save the occupancy maps.
        np.save(str(OCCUPANCY_MAPS_DIRECTORY.joinpath(filename).resolve()), o.occupancy_map)
        np.save(str(MAGNEBOT_OCCUPANCY_MAPS_DIRECTORY.joinpath(filename).resolve()), magnebot_occupancy_map)

    def run(self) -> None:
        """
        Create occupancy maps for each scene_layout combination.
        """

        for f in OCCUPANCY_MAPS_DIRECTORY.iterdir():
            if f.is_file():
                self.create(scene=f.name[:-6], layout=int(f.name[-5]))
        self.communicate({"$type": "terminate"})


if __name__ == "__main__":
    c = OccupancyMapper()
    c.run()
