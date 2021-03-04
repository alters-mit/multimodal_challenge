from json import dumps
from typing import Optional, List, Tuple
from tqdm import tqdm
import numpy as np
from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from tdw.output_data import Transforms, Raycast
from magnebot.scene_environment import SceneEnvironment
from magnebot.util import get_data
from multimodal_challenge.util import DROP_OBJECTS, get_object_init_commands, get_scene_librarian, get_drop_zones
from multimodal_challenge.paths import REHEARSAL_DIRECTORY, OBJECT_INIT_DIRECTORY
from multimodal_challenge.dataset.dataset_trial import DatasetTrial
from multimodal_challenge.dataset.drop_zone import DropZone
from multimodal_challenge.encoder import Encoder
from multimodal_challenge.multimodal_object_init_data import MultiModalObjectInitData


class Rehearsal(Controller):
    """
    "Rehearse" the audio dataset by running randomly-generated trials and saving the "valid" trials.

    This is meant only for backend developers; the Python module already has cached rehearsal data.

    Each scene has a corresponding list of [`DropZones`](../api/drop_zone.md). These are already cached.
    If the target object lands in a `DropZone`, then this was a valid trial.
    As a result, this script will cut down on dev time and generation time.

    There will be a small discrepancy in physics behavior when running `dataset.py` because in this controller,
    all objects are kinematic (non-moveable) in order to avoid re-initializing the scene per trial (which is slow).

    # Requirements

    - The `multimodal_challenge` Python module.

    # Usage

    1. `cd dataset`
    2. `python3 rehearsal.py`
    3. Run build

    # How it works

    **Per scene_layout combination** (i.e. scene `mm_kitchen_1_a` layout `0`):

    1. Load the corresponding object init data and `DropZone` data.
    2. Run trials per scene_layout combination until there's enough (for example, 2000 per scene_layout combination).

    **Per trial:**

    1. Randomly set the parameters of a new [`DatasetTrial`](../api/dataset_trial.md) for initialization.
    2. Let the target object fall. **The only output data is the `Transform` of the target object.**
    3. When the target object stops falling, if it's is in a `DropZone`, record the `DatasetTrial`.

    **Result:** A list of `DatasetTrial` initialization objects per scene_layout combination:

    ```
    D:/multimodal_challenge/dataset  # See dataset in config.ini
    ....drops/
    ........1_0.json  # scene_layout
    ........1_1.json
    ```
    """

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
        self.drop_object: Optional[int] = None
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
        """:field
        The drop zones for the current scene.
        """
        self.drop_zones: List[DropZone] = list()

    def do_trial(self) -> Tuple[Optional[DatasetTrial], int]:
        """
        Choose a random object. Assign a random (constrained) scale, position, rotation, and force.
        Let the object fall. When it stops moving, determine if the object is in a drop zone.

        :return: Tuple: A `DatasetTrial` if the object landed in the drop zone, otherwise None; drop zone ID.
        """

        commands = []
        if self.drop_object is not None:
            commands.append({"$type": "destroy_object",
                             "id": self.drop_object})
        # Get a random room.
        # Get a random starting position.
        position = {"x": float(self.rng.uniform(self.scene_environment.x_min, self.scene_environment.x_max)),
                    "y": 2.8,
                    "z": float(self.rng.uniform(self.scene_environment.z_min, self.scene_environment.z_max))}
        # Raycast down from the position.
        commands.append({"$type": "send_raycast",
                         "origin": position,
                         "destination": {"x": position["x"], "y": 0, "z": position["z"]}})
        resp = self.communicate(commands)
        raycast = get_data(resp=resp, d_type=Raycast)
        min_y = raycast.get_point()[1] + 0.2
        if min_y > position["y"]:
            min_y = raycast.get_point()[1]
        # Get a random y value for the starting position.
        position["y"] = self.rng.uniform(min_y, position["y"])
        commands.clear()
        # Get the next object.
        name = self.rng.choice(DROP_OBJECTS)
        # Get the init data.
        a = MultiModalObjectInitData(name=name,
                                     position=position,
                                     rotation={"x": float(self.rng.uniform(-360, 360)),
                                               "y": float(self.rng.uniform(-360, 360)),
                                               "z": float(self.rng.uniform(-360, 360))},
                                     kinematic=True)
        # Define the drop force.
        force = {"x": float(self.rng.uniform(-0.2, 0.2)),
                 "y": float(self.rng.uniform(-0.05, 0.05)),
                 "z": float(self.rng.uniform(-0.2, 0.2))}
        # Add the initialization commands.
        self.drop_object, object_commands = a.get_commands()
        commands.extend(object_commands)
        # Apply the force. Request Transforms data for this object.
        commands.extend([{"$type": "apply_force_to_object",
                          "id": self.drop_object,
                          "force": force},
                         {"$type": "send_transforms",
                          "ids": [self.drop_object],
                          "frequency": "always"}])
        # Send the commands!
        resp = self.communicate(commands)
        p_0 = np.array(get_data(resp=resp, d_type=Transforms).get_position(0))
        done = False
        good = False
        while not done:
            # Skip some frames because we only care about where the object lands, not its trajectory.
            # This will make the simulation much faster.
            resp = self.communicate([{"$type": "step_physics",
                                      "frames": 10}])
            p_1 = np.array(get_data(resp=resp, d_type=Transforms).get_position(0))
            # The object fell below the floor.
            if p_1[1] < -0.1:
                done = True
                good = False
            # The object stopped moving.
            elif np.linalg.norm(p_0 - p_1) < 0.001:
                done = True
                good = True
            p_0 = p_1
        if not good:
            return None, -1
        # Check if this object is in a drop zone.
        for i, drop_zone in enumerate(self.drop_zones):
            if drop_zone.center[1] + 0.1 >= p_0[1] >= drop_zone.center[1] and \
                    np.linalg.norm(p_0 - drop_zone.center) < drop_zone.radius:
                return DatasetTrial(init_data=a, force=force, position=TDWUtils.array_to_vector3(p_0)), i
        return None, -1

    def run(self, num_trials: int = 10000) -> None:
        """
        Generate results for each scene_layout combination.

        :param num_trials: The total number of trials.
        """

        self.scene_librarian = get_scene_librarian()
        scenes: List[str] = list()
        # Get the scene_layout schema.
        for f in OBJECT_INIT_DIRECTORY.iterdir():
            # Expected: mm_kitchen_1a_0.json, mm_kitchen_1a_1.json, ... , mm_kitchen_2b_2.json, ...
            if f.is_file() and f.suffix == ".json":
                scenes.append(f.name.replace(".json", ""))
        # Do trials for each scene_layout combination.
        trials_per_scene_layout = int(num_trials / float(len(scenes)))
        for scene in scenes:
            scene_name = scene[:-2]
            layout = int(scene[-1])
            self.do_trials(scene=scene_name, layout=layout, num_trials=trials_per_scene_layout)
        self.communicate({"$type": "terminate"})

    def do_trials(self, scene: str, layout: int, num_trials: int) -> None:
        """
        Load a scene_layout combination, and its objects, and its drop zones.
        Run random trials until we have enough "good" trials, where "good" means that the object landed in a drop zone.
        Save the result to disk.

        :param scene: The scene name.
        :param layout: The object layout variant of the scene.
        :param num_trials: How many trials we want to save to disk.
        """

        filename = f"{scene}_{layout}.json"
        self.drop_zones = get_drop_zones(filename=filename)
        scene_record = self.scene_librarian.get_record(scene)
        commands: List[dict] = [{"$type": "add_scene",
                                 "name": scene_record.name,
                                 "url": scene_record.get_url()},
                                {"$type": "send_environments"},
                                {"$type": "enable_reflection_probes",
                                 "enable": False}]
        commands.extend(get_object_init_commands(scene=scene, layout=layout))
        # Make all objects kinematic.
        for i in range(len(commands)):
            if commands[i]["$type"] == "set_kinematic_state":
                commands[i]["is_kinematic"] = True
        resp = self.communicate(commands)
        # Set the scene environment.
        self.scene_environment = SceneEnvironment(resp=resp)
        pbar = tqdm(total=num_trials)
        # Remember all good drops.
        dataset_trials: List[DatasetTrial] = list()
        drop_zone_indices: List[int] = list()
        while len(dataset_trials) < num_trials:
            # Do a trial.
            dataset_trial, drop_zone_index = self.do_trial()
            # If we got an object back, then this was a good trial.
            if dataset_trial is not None:
                # Save the data.
                dataset_trials.append(dataset_trial)
                drop_zone_indices.append(drop_zone_index)
                pbar.update(1)
        pbar.close()
        # Write the results to disk.
        REHEARSAL_DIRECTORY.joinpath(filename).write_text(dumps(dataset_trials, cls=Encoder), encoding="utf-8")
        # Record the drop zone indices for debugging.
        REHEARSAL_DIRECTORY.joinpath(f"{scene}_{layout}_drop_zones.json").write_text(dumps(drop_zone_indices),
                                                                                     encoding="utf-8")


if __name__ == "__main__":
    m = Rehearsal(random_seed=0)
    m.run(num_trials=1000)
