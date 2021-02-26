from pathlib import Path
from json import loads, dumps
from typing import Optional, List, Dict
from csv import DictReader
from tqdm import tqdm
import numpy as np
from tdw.controller import Controller
from tdw.output_data import Transforms, Raycast
from tdw.tdw_utils import TDWUtils
from magnebot.scene_environment import SceneEnvironment, Room
from magnebot.util import get_data
from multimodal_challenge.util import DROP_OBJECTS, get_object_init_commands, get_scene_librarian
from multimodal_challenge.paths import DROP_ZONE_DIRECTORY, SCENE_LAYOUT_PATH
from multimodal_challenge.dataset_generation.drop import Drop
from multimodal_challenge.dataset_generation.drop_zone import DropZone
from multimodal_challenge.encoder import Encoder
from multimodal_challenge.multimodal_object_init_data import MultiModalObjectInitData


class Rehearsal(Controller):
    """
    "Rehearse" the audio dataset_generation by running randomly-generated trials and saving the "valid" trials.

    This is meant only for backend developers; the Python module already has cached rehearsal data.

    Each scene has a corresponding list of [`DropZones`](../api/drop_zone.md). These are already cached. If the target object lands in a `DropZone`, then this was a valid trial. As a result, this script will cut down on dev time (we don't need to set drop parameters manually) and generation time (because we don't have to discard any audio recordings).

    # Requirements

    - The `multimodal_challenge` Python module.

    # Usage

    1. `cd dataset_generation`
    2. `python3 rehearsal.py`
    3. Run build

    # How it works

    **Per scene_layout combination** (i.e. scene `mm_kitchen_1_a` layout `0`):

    1. Load the corresponding object init data and `DropZone` data.
    2. Run trials per scene_layout combination until there's enough (for example, 2000 per scene_layout combination).

    **Per trial:**

    1. Randomly set the parameters of a new [`Drop`](../api/drop.md) which is used here as initialization data.
    2. Let the target object fall. **The only output data is the `Transform` of the target object.**
    3. When the target object stops falling, check if the target object is in a `DropZone`. If so, record the `Drop`.

    **Result:** A list of `Drop` initialization objects per scene_layout combination:

    ```
    multimodal_challenge/
    ....data/
    ........objects/
    ........scenes/
    ........dataset/
    ............drops/
    ................1_0.json  # scene_layout
    ................1_1.json
    ```

    ### Advantages

    - This is a VERY fast process. It saves dev time (we don't need to manually set trial init values) and audio recording time (we don't need to discard any recordings).

    ### Disadvantages

    - All objects in the scene are kinematic because re-initializing the scene per trial would be too slow. Therefore, there will be a small discrepancy between physics behavior in the rehearsal and physics behavior in the dataset.

    """

    def __init__(self, port: int = 1071, random_seed: int = None,
                 output_directory: str = "D:/multimodal_challenge/drops"):
        """
        Create the network socket and bind the socket to the port.

        :param port: The port number.
        :param random_seed: The seed used for random numbers. If None, this is chosen randomly.
        :param output_directory: The root output directory.
        """

        super().__init__(port=port, launch_build=False, check_version=True)
        """:field
        The ID of the dropped object. This changes per trial.
        """
        self.drop_object: Optional[int] = None
        # Get a random seed.
        if random_seed is None:
            random_seed = self.get_unique_id()
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
        """:field
        The root output directory.
        """
        self.output_directory: Path = Path(output_directory)
        if not self.output_directory.exists():
            self.output_directory.mkdir(parents=True)

    def do_trial(self) -> Optional[Drop]:
        """
        Choose a random object. Assign a random (constrained) scale, position, rotation, and force.
        Let the object fall. When it stops moving, determine if the object is in a drop zone.

        :return: If the object is in the drop zone, a `Drop` object of trial initialization parameters. Otherwise, None.
        """

        commands = []
        if self.drop_object is not None:
            commands.append({"$type": "destroy_object",
                             "id": self.drop_object})
        # Get a random room.
        room: Room = self.rng.choice(self.scene_environment.rooms)
        # Get a random starting position.
        position = {"x": float(self.rng.uniform(room.x_0, room.x_1)),
                    "y": 2.8,
                    "z": float(self.rng.uniform(room.z_0, room.z_1))}
        # Raycast down from the position.
        commands.append({"$type": "send_raycast",
                         "origin": position,
                         "destination": {"x": position["x"], "y": 0, "z": position["z"]}})
        resp = self.communicate(commands)
        raycast = get_data(resp=resp, d_type=Raycast)
        min_y = raycast.get_point()[1] + 0.5
        if min_y > position["y"]:
            min_y = raycast.get_point()[1]
        # Get a random y value for the starting position.
        position["y"] = self.rng.uniform(min_y, position["y"])
        commands.clear()
        # Get the next object.
        name = self.rng.choice(DROP_OBJECTS)
        scale = float(self.rng.uniform(0.75, 1.2))
        # Get the init data.
        a = MultiModalObjectInitData(name=name,
                                     scale_factor={"x": scale, "y": scale, "z": scale},
                                     position=position,
                                     rotation={"x": float(self.rng.uniform(-360, 360)),
                                               "y": float(self.rng.uniform(-360, 360)),
                                               "z": float(self.rng.uniform(-360, 360))},
                                     gravity=True,
                                     kinematic=False)
        # Define the drop force.
        force = {"x": float(self.rng.uniform(-0.2, 0.2)),
                 "y": float(self.rng.uniform(-0.2, 0.1)),
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
            return None
        # Check if this object is in a drop zone.
        for drop_zone in self.drop_zones:
            if drop_zone.center[1] + 0.1 >= p_0[1] >= drop_zone.center[1] and \
                    np.linalg.norm(p_0 - drop_zone.center) < drop_zone.radius:
                return Drop(init_data=a, force=force)
        return None

    def run(self, num_trials: int = 10000) -> None:
        """
        Generate results for each scene_layout combination.

        :param num_trials: The total number of trials.
        """

        self.scene_librarian = get_scene_librarian()
        scene_layouts: Dict[str, int] = dict()
        num_layouts: int = 0
        with open(str(SCENE_LAYOUT_PATH.resolve()), newline='') as f:
            reader = DictReader(f)
            for row in reader:
                layouts = int(row["layout"])
                scene_layouts[row["scene"]] = layouts
                num_layouts += layouts
        for scene in scene_layouts:
            for i in range(scene_layouts[scene]):
                self.do_trials(scene=scene, layout=i, num_trials=int(num_trials / num_layouts))

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
        # Get the drop zones.
        drop_zone_data = loads(DROP_ZONE_DIRECTORY.joinpath(filename).read_text(encoding="utf-8"))
        self.drop_zones.clear()
        for drop_zone in drop_zone_data["drop_zones"]:
            self.drop_zones.append(DropZone(center=TDWUtils.vector3_to_array(drop_zone["position"]),
                                            radius=drop_zone["size"]))
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
        drops: List[Drop] = list()
        try:
            while len(drops) < num_trials:
                # Do a trial.
                drop: Drop = self.do_trial()
                # If we got an object back, then this was a good trial.
                if drop is not None:
                    # Save the data.
                    drops.append(drop)
                    pbar.update(1)
        finally:
            pbar.close()
            # Write the results to disk.
            self.output_directory.joinpath(filename).write_text(dumps(drops, cls=Encoder, indent=2), encoding="utf-8")


if __name__ == "__main__":
    m = Rehearsal()
    m.run()
