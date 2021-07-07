from typing import List, Dict, Optional
from pathlib import Path
import numpy as np
from tdw.output_data import Transforms
from tdw.tdw_utils import TDWUtils
from magnebot.constants import OCCUPANCY_CELL_SIZE
from magnebot.util import get_data
from multimodal_challenge.paths import DISTRACTORS_DIRECTORY, OCCUPANCY_MAPS_DIRECTORY, DISTRACTOR_OBJECTS_PATH
from multimodal_challenge.multimodal_object_init_data import MultiModalObjectInitData, TransformInitData
from multimodal_challenge.dataset.rehearsal_base import RehearsalBase
from multimodal_challenge.dataset.distractor_trial import DistractorTrial


class Distractors(RehearsalBase, DistractorTrial):
    """
    Add distractors to the scene. Per trial, drop distractors onto empty areas of the occupancy map.
    """

    """:class_var
    The maximum distance from the center of the room that a distractor can be placed.
    """
    DISTANCE_FROM_CENTER: float = 0.7
    """:class_var
    The minimum number of distractors in the scene.
    """
    MIN_DISTRACTORS: int = 6
    """:class_var
    The maximum number of distractors in the scene.
    """
    MAX_DISTRACTORS: int = 12
    """:class_var
    The minimum y value for the initial position of a distractor object.
    """
    MIN_DROP_Y: float = 1.5
    """:class_var
    The maximum y value for the initial position of a distractor object.
    """
    MAX_DROP_Y: float = 2.8
    """:class_var
    The amount of frames skipped while objects are falling.
    """
    SKIPPED_FRAMES: int = 20

    def __init__(self, port: int = 1071, random_seed: int = None):
        """
        :param port: The socket port for connecting to the build.
        :param random_seed: The random seed. If None, a seed will be generated.
        """

        super().__init__(port=port, random_seed=random_seed)
        """:field
        The occupancy map for the scene. This will be used to place the objects.
        """
        self.occupancy_map: np.array = np.array([0])
        lib = list(TransformInitData.LIBRARIES.values())[-1]
        """:field
        Metadata for distractor objects.
        """
        self.distractors: List[str] = [lib.get_record(d).name for d in
                                       DISTRACTOR_OBJECTS_PATH.read_text().strip().split("\n")]

    def _get_output_directory(self) -> Path:
        return DISTRACTORS_DIRECTORY

    def _set_potential_object_positions(self, scene: str, layout: int) -> None:
        self.occupancy_map = np.load(str(OCCUPANCY_MAPS_DIRECTORY.joinpath(f"{scene}_{layout}.npy").resolve()))

    def _do_trial(self) -> Optional[DistractorTrial]:
        ids: List[int] = list()
        names: List[str] = list()
        spawn_positions = list()
        # Get the maximum distance from the center of the room that the objects can be dropped at.
        max_distance = Distractors.DISTANCE_FROM_CENTER * min([np.abs(self.scene_environment.x_min),
                                                               self.scene_environment.x_max,
                                                               np.abs(self.scene_environment.z_min),
                                                               self.scene_environment.z_max])
        origin = np.array([0, 0])
        for ix, iy in np.ndindex(self.occupancy_map.shape):
            if self.occupancy_map[ix][iy] != 0:
                continue
            x = self.scene_environment.x_min + (ix * OCCUPANCY_CELL_SIZE)
            z = self.scene_environment.z_min + (iy * OCCUPANCY_CELL_SIZE)
            p = np.array([x, z])
            if np.linalg.norm(p - origin) <= max_distance:
                spawn_positions.append(np.array([x, z]))
        spawn_positions: np.array = np.array(spawn_positions)
        # Randomly shuffle the positions.
        self.rng.shuffle(spawn_positions)
        # Get some distractors.
        num_distractors: int = self.rng.randint(Distractors.MIN_DISTRACTORS, Distractors.MAX_DISTRACTORS + 1)
        if num_distractors >= len(spawn_positions):
            num_distractors = len(spawn_positions) - 1

        good = True
        # Drop the distractors one at a time to avoid interpentration.
        # Each time, make sure that the distractors actually stop moving and actually land above floor level.
        for i in range(num_distractors):
            drop_position = {"x": float(spawn_positions[i][0]) + float(self.rng.uniform(-OCCUPANCY_CELL_SIZE * 0.5,
                                                                                        OCCUPANCY_CELL_SIZE * 0.5)),
                             "y": float(self.rng.uniform(Distractors.MIN_DROP_Y, Distractors.MAX_DROP_Y)),
                             "z": float(spawn_positions[i][1]) + float(self.rng.uniform(-OCCUPANCY_CELL_SIZE * 0.5,
                                                                                        OCCUPANCY_CELL_SIZE * 0.5))}
            name = self.distractors[self.rng.randint(0, len(self.distractors))]
            names.append(name)
            init_data: MultiModalObjectInitData = MultiModalObjectInitData(
                name=name,
                position=drop_position,
                rotation={"x": float(self.rng.uniform(-360, 360)),
                          "y": float(self.rng.uniform(-360, 360)),
                          "z": float(self.rng.uniform(-360, 360))},
                kinematic=False)
            # Get the commands and the object ID.
            o_id, commands = init_data.get_commands()
            ids.append(o_id)
            # Request Transforms data per frame for this object only.
            commands.extend([{"$type": "send_transforms",
                              "frequency": "always",
                              "ids": [o_id]},
                             {"$type": "step_physics",
                              "frames": Distractors.SKIPPED_FRAMES}])
            resp = self.communicate(commands)
            position_0 = Distractors._get_position(resp=resp)
            done = False
            num_frames = 0
            while not done:
                # Skip some frames because we only care about where the objects land.
                resp = self.communicate([{"$type": "step_physics",
                                          "frames": Distractors.SKIPPED_FRAMES}])
                position_1 = Distractors._get_position(resp=resp)
                # If the object is below the floor, this is a bad trial.
                if position_1[1] < -0.1:
                    done = True
                    good = False
                # If the object stopped moving, this is a (potentially) good trial.
                elif np.linalg.norm(position_0 - position_1) <= 0.001:
                    done = True
                # The object is still moving.
                else:
                    num_frames += 1
                    position_0 = position_1
                    # If the trial took too long, something weird happened. Discard the trial.
                    if num_frames >= 1000:
                        done = True
                        good = False
        # Get the transforms of each of the distractor objects.
        resp = self.communicate({"$type": "send_transforms",
                                 "frequency": "once",
                                 "ids": ids})
        # Remove the distractor objects.
        self.communicate([{"$type": "destroy_object", "id": o_id} for o_id in ids])
        # If this isn't a good trial, stop here.
        if not good:
            print("bad")
            return None
        # Get all of the positions.
        tr = get_data(resp=resp, d_type=Transforms)
        distractor_positions: List[Dict[str, float]] = list()
        distractor_rotations: List[Dict[str, float]] = list()
        for name, object_id in zip(names, ids):
            for i in range(tr.get_num()):
                if tr.get_id(i) == object_id:
                    distractor_positions.append(TDWUtils.array_to_vector3(tr.get_position(i)))
                    distractor_rotations.append(TDWUtils.array_to_vector4(tr.get_rotation(i)))
        # Return the trial data.
        return DistractorTrial(names=names, positions=distractor_positions, rotations=distractor_rotations)

    @staticmethod
    def _get_position(resp: List[bytes]) -> np.array:
        """
        :param resp: The response from the build.

        :return: The position of the distractor object currently being dropped.
        """

        return np.array(get_data(resp=resp, d_type=Transforms).get_position(0))


if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("--num_trials", type=int, default=10000, help="The total number of trials.")
    parser.add_argument("--random_seed", type=int, default=0, help="The random seed.")
    args = parser.parse_args()
    m = Distractors(random_seed=args.random_seed)
    m.run(num_trials=args.num_trials)
