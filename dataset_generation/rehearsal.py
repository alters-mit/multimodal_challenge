from json import dumps
from typing import Optional, List, Dict
from tqdm import tqdm
import numpy as np
from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from tdw.output_data import Transforms
from tdw.object_init_data import TransformInitData
from magnebot.scene_environment import SceneEnvironment
from magnebot.constants import OCCUPANCY_CELL_SIZE
from magnebot.util import get_data
from multimodal_challenge.util import TARGET_OBJECTS, get_object_init_commands, get_scene_librarian, get_scene_layouts
from multimodal_challenge.paths import REHEARSAL_DIRECTORY, OCCUPANCY_MAPS_DIRECTORY, DISTRACTOR_OBJECTS_PATH
from multimodal_challenge.dataset.dataset_trial import DatasetTrial
from multimodal_challenge.encoder import Encoder
from multimodal_challenge.multimodal_object_init_data import MultiModalObjectInitData


class Rehearsal(Controller):
    """
    "Rehearse" the audio dataset by running randomly-generated trials and saving the "valid" trials.

    This is meant only for backend developers; the Python module already has cached rehearsal data.

    Per trial, a random number of random "distractor objects" will be dropped on the floor.
    Then, a random "target object" will be dropped on the floor.

    The trial is considered good if all of the objects land on a surface and stop moving after a reasonable length of time; if not, the trial is discarded.

    There will be a small discrepancy in physics behavior when running `dataset.py` because in this controller,
    all objects are kinematic (non-moveable) in order to avoid re-initializing the scene per trial (which is slow).

    # Requirements

    - The `multimodal_challenge` Python module.

    # Usage

    1. `cd dataset`
    2. `[ENV VARIABLES] python3 rehearsal.py [ARGUMENTS]`
    3. Run build

    ## Environment variables

    #### 1. `MULTIMODAL_ASSET_BUNDLES`

    **The root directory to download scenes and asset bundles from.** Default value: `"https://tdw-public.s3.amazonaws.com"`

    Every scene (room environment) and model (furniture, cabinets, cups, etc.) is stored in TDW as an [asset bundle](https://docs.unity3d.com/Manual/AssetBundlesIntro.html). These asset bundles are downloaded at runtime from a remote S3 server, but it is possible to download them *before* run time and load them locally. **If your Internet connection will make it difficult/slow/impossible to download large US-based files at runtime, we strongly suggest you download them locally.** To do this:

    1. `cd path/to/multimodal_challenge`
    2. `python3 download.py --dst [DST]`. The `--dst` argument sets the root download directory. Example: `python3 download.py --dst /home/mm_asset_bundles`.

    #### 2. `MULTIMODAL_DATASET`

    **The directory where the Trial files will be saved.** Default value: `"D:/multimodal_challenge"`

    #### How to set the environment variables

    Replace `[asset_bundles]` and `[dataset]` with the actual paths. For example: `export MULTIMODAL_ASSET_BUNDLES=/home/mm_asset_bundles`.

    | Platform             | Command                                                      |
    | -------------------- | ------------------------------------------------------------ |
    | OS X or Linux        | `export MULTIMODAL_ASSET_BUNDLES=[asset_bundles] && export MULTIMODAL_DATASET=[dataset] && python3 rehearsal.py` |
    | Windows (cmd)        | `set MULTIMODAL_ASSET_BUNDLES=[asset_bundles] && set MULTIMODAL_DATASET=[dataset] && py -3 rehearsal.py` |
    | Windows (powershell) | `$env:MULTIMODAL_ASSET_BUNDLES="[asset_bundles]" ; $env:MULTIMODAL_DATASET="[dataset]" ; py -3 rehearsal.py` |

    ## Arguments

    | Argument | Default | Description |
    | --- | --- | --- |
    | `--random_seed` | 0 | The random seed. |
    | `--num_trials` | 10000 | Generate this many trials. |

    Example: `python3 rehearsal.py --random_seed 12345 --num_trials 300`

    # How it works

    **Per scene_layout combination** (i.e. scene `mm_kitchen_1_a` layout `0`):

    1. Load the corresponding object init data.
    2. Run trials per scene_layout combination until there's enough (for example, 2000 per scene_layout combination).

    **Per trial:**

    1. Randomly set the parameters of a new [`DatasetTrial`](../api/dataset_trial.md) for initialization.
    2. Let each distractor object fall, one at a time (to avoid interpentration). If the objects fall in acceptable positions, continue.
    3. Let the target object fall.
    4. If the target object is in an acceptable position, generate a `DatasetTrial` object.

    **Result:** A list of `DatasetTrial` initialization objects per scene_layout combination:

    ```
    D:/multimodal_challenge/
    ....rehearsal/
    ........mm_kitchen_1a_0.json  # scene_layout
    ........mm_kitchen_1a_1.json
    ........(etc.)
    ```
    """

    """:class_var
    The maximum distance from the center of the room that an object can be placed.
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
    The minimum y value for the initial position of an object.
    """
    MIN_DROP_Y: float = 1.5
    """:class_var
    The maximum y value for the initial position of an object.
    """
    MAX_DROP_Y: float = 2.8
    """:class_var
    The amount of frames skipped while objects are falling.
    """
    SKIPPED_FRAMES: int = 20

    def __init__(self, port: int = 1071, random_seed: int = None):
        """
        Create the network socket and bind the socket to the port.

        :param port: The port number.
        :param random_seed: The seed used for random numbers. If None, this is chosen randomly.
        """

        super().__init__(port=port, launch_build=False, check_version=True)
        """:field
        The ID of the dropped object. This changes per trial.
        """
        self.target_object_id: Optional[int] = None
        # Get a random seed.
        if random_seed is None:
            random_seed = self.get_unique_id()
        # Write the random seed.
        REHEARSAL_DIRECTORY.joinpath("seed.txt").write_text(str(random_seed), encoding="utf-8")
        """:field
        The random number generator.
        """
        self.rng: np.random.RandomState = np.random.RandomState(random_seed)
        """:field
        Environment data used for setting drop positions.
        """
        self.scene_environment: Optional[SceneEnvironment] = None
        lib = list(TransformInitData.LIBRARIES.values())[-1]
        """:field
        Metadata for distractor objects.
        """
        self.distractors: List[str] = [lib.get_record(d).name for d in
                                       DISTRACTOR_OBJECTS_PATH.read_text().strip().split("\n")]
        """:field
        A list of all possible initial object positions per trial.
        """
        self.object_positions: List[np.array] = list()

    def do_trial(self) -> Optional[DatasetTrial]:
        """
        Choose a random object. Assign a random (constrained) scale, position, rotation, and force.
        Let the object fall. When it stops moving, determine if the object is in a drop zone.

        :return: A `DatasetTrial` if this is a good trial.
        """

        # Randomize the starting positions.
        self.rng.shuffle(self.object_positions)

        # Add some distractors to the scene.
        num_distractors: int = self.rng.randint(Rehearsal.MIN_DISTRACTORS, Rehearsal.MAX_DISTRACTORS + 1)
        if num_distractors >= len(self.object_positions):
            num_distractors = len(self.object_positions) - 1

        # Remember the IDs and names of the distractors.
        distractor_ids: List[int] = list()
        distractor_names: Dict[int, str] = dict()
        # This flag is used to determine if whether we should immediately discard the trial.
        good = True
        # Drop the distractors one at a time to avoid interpentration.
        # Each time, make sure that the distractors actually stop moving and actually land above floor level.
        for i in range(num_distractors):
            name = self.distractors[self.rng.randint(0, len(self.distractors))]
            init_data: MultiModalObjectInitData = MultiModalObjectInitData(
                name=name,
                position=self._get_position(i),
                rotation=self._get_rotation(),
                kinematic=False)
            # Get the commands and the object ID.
            o_id, commands = init_data.get_commands()
            distractor_names[o_id] = name
            distractor_ids.append(o_id)
            # Request Transforms data per frame for this object only.
            commands.extend([{"$type": "send_transforms",
                              "frequency": "always",
                              "ids": [o_id]},
                             {"$type": "step_physics",
                              "frames": Rehearsal.SKIPPED_FRAMES}])
            resp = self.communicate(commands)
            good = self._wait_for_object_to_fall(resp=resp)
            if not good:
                break
        # A list of commands for destroying the non-floorplan objects in the scene.
        destroy_objects = [{"$type": "destroy_object", "id": o_id} for o_id in distractor_ids]
        # If this isn't a good trial, stop here.
        if not good:
            # Remove the distractor objects.
            self.communicate(destroy_objects)
            return None
        # Get the next object.
        name = self.rng.choice(TARGET_OBJECTS)
        # Get the init data.
        a = MultiModalObjectInitData(name=name,
                                     position=self._get_position(len(self.object_positions) - 1),
                                     rotation=self._get_rotation(),
                                     kinematic=False)
        # Define the drop force.
        force = {"x": float(self.rng.uniform(-0.1, 0.1)),
                 "y": float(self.rng.uniform(-0.05, 0.05)),
                 "z": float(self.rng.uniform(-0.1, 0.1))}
        # Add the initialization commands.
        self.target_object_id, commands = a.get_commands()
        # Apply the force. Request Transforms data for this object.
        commands.extend([{"$type": "apply_force_to_object",
                          "id": self.target_object_id,
                          "force": force},
                         {"$type": "send_transforms",
                          "ids": [self.target_object_id],
                          "frequency": "always"}])
        # Send the commands!
        resp = self.communicate(commands)
        # Wait for the object to finish falling.
        good = self._wait_for_object_to_fall(resp=resp)
        # Get the transform data.
        object_ids = distractor_ids[:]
        object_ids.append(self.target_object_id)
        resp = self.communicate({"$type": "send_transforms",
                                 "frequency": "once",
                                 "ids": object_ids})
        # Destroy all non-floorplan objects.
        destroy_objects.append({"$type": "destroy_object",
                                "id": self.target_object_id})
        self.communicate(destroy_objects)
        if not good:
            return None
        distractor_init_data: List[MultiModalObjectInitData] = list()
        target_object_position: Dict[str, float] = dict()
        tr = Transforms(resp[0])
        for i in range(tr.get_num()):
            object_id = tr.get_id(i)
            if object_id == self.target_object_id:
                target_object_position = TDWUtils.array_to_vector3(tr.get_position(i))
            # Get distractor initialization data.
            elif object_id in distractor_ids:
                distractor_init_data.append(MultiModalObjectInitData(name=distractor_names[object_id],
                                                                     position=TDWUtils.array_to_vector3(
                                                                         tr.get_position(i)),
                                                                     rotation=TDWUtils.array_to_vector4(
                                                                         tr.get_rotation(i))))
        # We don't want the target object to fall right away.
        a.kinematic = True
        return DatasetTrial(target_object=a, force=force, target_object_position=target_object_position,
                            distractors=distractor_init_data)

    def run(self, num_trials: int = 10000) -> None:
        """
        Generate results for each scene_layout combination.

        :param num_trials: The total number of trials.
        """

        self.scene_librarian = get_scene_librarian()
        # Get the total number of scene_layout combinations.
        scene_layouts = get_scene_layouts()
        num_layouts = 0.0
        for k in scene_layouts:
            num_layouts += scene_layouts[k]
        # Do trials for each scene_layout combination.
        trials_per_scene_layout = int(np.ceil(num_trials / num_layouts))
        pbar = tqdm(total=int(trials_per_scene_layout * num_layouts))
        for scene in scene_layouts:
            for layout in range(scene_layouts[scene]):
                self.do_trials(scene=scene, layout=layout, num_trials=trials_per_scene_layout, pbar=pbar)
        pbar.close()
        self.communicate({"$type": "terminate"})

    def do_trials(self, scene: str, layout: int, num_trials: int, pbar: tqdm = None) -> None:
        """
        Load a scene_layout combination, and its objects, and its drop zones.
        Run random trials until we have enough "good" trials, where "good" means that the object landed in a drop zone.
        Save the result to disk.

        :param scene: The scene name.
        :param layout: The object layout variant of the scene.
        :param num_trials: How many trials we want to save to disk.
        :param pbar: Progress bar.
        """

        scene_record = self.scene_librarian.get_record(scene)
        commands: List[dict] = [{"$type": "add_scene",
                                 "name": scene_record.name,
                                 "url": scene_record.get_url()},
                                {"$type": "send_environments"},
                                {"$type": "enable_reflection_probes",
                                 "enable": False},
                                {"$type": "destroy_all_objects"}]
        commands.extend(get_object_init_commands(scene=scene, layout=layout))
        # Make all objects kinematic.
        for i in range(len(commands)):
            if commands[i]["$type"] == "set_kinematic_state":
                commands[i]["is_kinematic"] = True
        resp = self.communicate(commands)
        # Set the scene environment.
        self.scene_environment = SceneEnvironment(resp=resp)

        # Get all object positions. A valid position is a free position not too far from the center of the room.
        self.object_positions.clear()
        # Get the occupancy map.
        occupancy_map: np.array = np.load(str(OCCUPANCY_MAPS_DIRECTORY.joinpath(f"{scene}_{layout}.npy").resolve()))
        # Get the maximum distance from the center of the room that the objects can be dropped at.
        max_distance = Rehearsal.DISTANCE_FROM_CENTER * min([np.abs(self.scene_environment.x_min),
                                                             self.scene_environment.x_max,
                                                             np.abs(self.scene_environment.z_min),
                                                             self.scene_environment.z_max])
        origin = np.array([0, 0])
        for ix, iy in np.ndindex(occupancy_map.shape):
            if occupancy_map[ix][iy] != 0:
                continue
            x = self.scene_environment.x_min + (ix * OCCUPANCY_CELL_SIZE)
            z = self.scene_environment.z_min + (iy * OCCUPANCY_CELL_SIZE)
            p = np.array([x, z])
            if np.linalg.norm(p - origin) <= max_distance:
                self.object_positions.append(np.array([x, z]))

        close_bar = pbar is None
        if pbar is None:
            pbar = tqdm(total=num_trials)
        pbar.set_description(f"{scene}_{layout}")
        # Remember all good drops.
        dataset_trials: List[DatasetTrial] = list()
        while len(dataset_trials) < num_trials:
            # Do a trial.
            dataset_trial = self.do_trial()
            # If we got an object back, then this was a good trial.
            if dataset_trial is not None:
                # Save the data.
                dataset_trials.append(dataset_trial)
                pbar.update(1)
        # Write the results to disk.
        REHEARSAL_DIRECTORY.joinpath(f"{scene}_{layout}.json").write_text(dumps(dataset_trials, cls=Encoder),
                                                                          encoding="utf-8")
        if close_bar:
            pbar.close()

    @staticmethod
    def _get_distractor_position(resp: List[bytes]) -> np.array:
        """
        :param resp: The response from the build.

        :return: The position of the distractor object currently being dropped.
        """

        return np.array(get_data(resp=resp, d_type=Transforms).get_position(0))

    def _get_position(self, i: int) -> Dict[str, float]:
        return {"x": float(self.object_positions[i][0]) + float(self.rng.uniform(-OCCUPANCY_CELL_SIZE * 0.5,
                                                                                 OCCUPANCY_CELL_SIZE * 0.5)),
                "y": float(self.rng.uniform(Rehearsal.MIN_DROP_Y, Rehearsal.MAX_DROP_Y)),
                "z": float(self.object_positions[i][1]) + float(self.rng.uniform(-OCCUPANCY_CELL_SIZE * 0.5,
                                                                                 OCCUPANCY_CELL_SIZE * 0.5))}

    def _get_rotation(self) -> Dict[str, float]:
        return {"x": float(self.rng.uniform(-360, 360)),
                "y": float(self.rng.uniform(-360, 360)),
                "z": float(self.rng.uniform(-360, 360))}

    def _wait_for_object_to_fall(self, resp: List[bytes]) -> bool:
        position_0 = Rehearsal._get_distractor_position(resp=resp)
        num_frames = 0
        while num_frames < 1000:
            # Skip some frames because we only care about where the objects land.
            resp = self.communicate([{"$type": "step_physics",
                                      "frames": Rehearsal.SKIPPED_FRAMES}])
            position_1 = Rehearsal._get_distractor_position(resp=resp)
            # If the object is below the floor, this is a bad trial.
            if position_1[1] < -0.1:
                return False
            # If the object stopped moving, this is a (potentially) good trial.
            elif np.linalg.norm(position_0 - position_1) <= 0.001:
                return True
            # The object is still moving.
            else:
                num_frames += 1
                position_0 = position_1
        # The object took too long to fall.
        return False


if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("--num_trials", type=int, default=10000, help="The total number of trials.")
    parser.add_argument("--random_seed", type=int, default=0, help="The random seed.")
    args = parser.parse_args()
    m = Rehearsal(random_seed=args.random_seed)
    m.run(num_trials=args.num_trials)
