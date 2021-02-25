from json import loads, dumps
from typing import Optional, List, Dict
from csv import DictReader
from tqdm import tqdm
import numpy as np
from tdw.controller import Controller
from tdw.py_impact import ObjectInfo
from tdw.output_data import Transforms
from magnebot.scene_environment import SceneEnvironment, Room
from magnebot.util import get_data
from multimodal_challenge.util import DROP_OBJECTS, get_object_init_commands, get_scene_librarian
from multimodal_challenge.paths import DROP_ZONE_DIRECTORY, AUDIO_DATASET_DROPS_DIRECTORY, SCENE_LAYOUT_PATH
from multimodal_challenge.dataset_generation.drop import Drop
from multimodal_challenge.dataset_generation.drop_zone import DropZone
from multimodal_challenge.encoder import Encoder
from multimodal_challenge.multimodal_object_init_data import MultiModalObjectInitData


class Rehearsal(Controller):
    """
    "Rehearse" the audio dataset_generation by running a series of random trials.

    Per scenes_layout combination, all of the objects are made kinematic. A target object is dropped.
    Each scene_layout combination has a number of "drop zones" which are stored in `data/scenes/drop_zones/`
    If the target object lands in a drop zone, then this is a "good" trial and the result is recorded.

    After a target number of good "drops" has been reached, the parameters used to initialize the trial are saved.
    They will be used for the actual dataset_generation generation.

    Advantages to this system:

    - We can randomly choose start parameters but because we're only recording 1 Transform, this will be VERY fast.
    - We can procedurally generate scenarios to avoid having to choose them by hand.

    Disadvantage to this system:

    - Each object is kinematic to make scene re-initialization as fast as possible.
      However, this means that there will be a discrepancy between the physics behavior in the rehearsal and the actual
      physics behavior in the dataset_generation generation. Ideally, the discrepancy is quite minimal.
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
        # Get the next object.
        name = self.rng.choice(DROP_OBJECTS)
        scale = float(self.rng.uniform(0.75, 1.2))
        room: Room = self.rng.choice(self.scene_environment.rooms)
        # Get the init data.
        a = MultiModalObjectInitData(name=name,
                                     scale_factor={"x": scale, "y": scale, "z": scale},
                                     position={"x": float(self.rng.uniform(room.x_0, room.x_1)),
                                               "y": float(self.rng.uniform(3, 3.8)),
                                               "z": float(self.rng.uniform(room.z_0, room.z_1))},
                                     rotation={"x": float(self.rng.uniform(-360, 360)),
                                               "y": float(self.rng.uniform(-360, 360)),
                                               "z": float(self.rng.uniform(-360, 360))},
                                     gravity=True,
                                     kinematic=False,
                                     audio=self._get_audio_info())
        # Define the drop force.
        force = {"x": float(self.rng.uniform(-8, 8)),
                 "y": float(self.rng.uniform(-20, 10)),
                 "z": float(self.rng.uniform(-8, 8))}
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
            resp = self.communicate([])
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
                    np.linalg.norm(p_0, drop_zone.center) < drop_zone.radius:
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

        # Get the drop zones.
        filename = f"{scene}_{layout}.json"
        drop_zone_data = loads(DROP_ZONE_DIRECTORY.joinpath(filename).read_text(encoding="utf-8"))
        self.drop_zones.clear()
        for drop_zone in drop_zone_data["drop_zones"]:
            self.drop_zones.append(DropZone(**drop_zone))
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
        drops: List[Drop] = list()
        pbar = tqdm(total=num_trials)
        while len(drops) < num_trials:
            # Do a trial.
            drop: Drop = self.do_trial()
            # If we got an object back, then this was a good trial.
            if drop is not None:
                drops.append(drop)
                pbar.update(1)
        pbar.close()
        # Save the drop data as a json file.
        AUDIO_DATASET_DROPS_DIRECTORY.joinpath(filename).write_text(dumps({"drops": drops}, cls=Encoder),
                                                                    encoding="utf-8")

    def _get_audio_info(self) -> ObjectInfo:
        # TODO
        raise Exception()
