from time import sleep
from typing import List, Optional
from pathlib import Path
from json import loads, dumps
from array import array
import numpy as np
import pyaudio
from tqdm import tqdm
from scipy.signal import convolve2d
from tdw.tdw_utils import AudioUtils, TDWUtils
from tdw.py_impact import PyImpact, ObjectInfo, AudioMaterial
from tdw.output_data import Rigidbodies, Transforms, AudioSources
from magnebot import ActionStatus
from magnebot.scene_state import SceneState
from magnebot.util import get_data
from multimodal_challenge.multimodal_base import MultiModalBase
from multimodal_challenge.paths import REHEARSAL_DIRECTORY, ENV_AUDIO_MATERIALS_PATH, DATASET_DIRECTORY
from multimodal_challenge.util import get_object_init_commands, get_scene_layouts, get_trial_filename
from multimodal_challenge.multimodal_object_init_data import MultiModalObjectInitData
from multimodal_challenge.trial import Trial
from multimodal_challenge.encoder import Encoder
from multimodal_challenge.dataset.dataset_trial import DatasetTrial
from multimodal_challenge.dataset.env_audio_materials import EnvAudioMaterials


class Dataset(MultiModalBase):
    """
    Use the initialization data generated by [`rehearsal.py`](rehearsal.md) to create [`Trials`](../api/trial.md). A `Trial` is initialization data for each object in the scene (position, rotation, etc.), initialization data for the Magenbot, and a .wav file.

    # Requirements

    - The `multimodal_challenge` Python module
    - Optional: Run [`rehearsal.py`](rehearsal.md) to generate the initialization data (there is already cached data in the Python module)
    - Audio drivers
    - [`PyAudio`](https://people.csail.mit.edu/hubert/pyaudio/) If you're using Windows and Python 3.7 or later, use a wheel from [this site](https://www.lfd.uci.edu/~gohlke/pythonlibs/) and install it via: `pip3 install path/to/the/downloaded.whl` (replace this with the actual path to the downloaded file)

    # Usage

    1. `cd dataset`
    2. `python3 dataset.py [ARGUMENTS]`
    3. Run build

    | Argument | Default | Description |
    | --- | --- | --- |
    | `--asset_bundles` | https://tdw-public.s3.amazonaws.com | Root local directory or remote URL of asset bundles. |
    | `--dataset_directory` | D:/multimodal_challenge | Root local directory of the dataset files. |
    | `--random_seed` | 0 | The random seed. |

    **This is a VERY long process.**

    # How it works

    **Per scene_layout combination:**

    1. Load the corresponding object init data and the [`DatasetTrial`](../api/dataset_trial.md) data from rehearsal.py

    **Per trial:**

    1. Re-initialize the scene.
    2. Select the next `DatasetTrial` initialization object in the list.
    3. Add a Magnebot. Turn the Magnebot away from `DatasetTrial.position`. Set random position and rotation parameters.
    4. Add the target object from the `DatasetTrial` parameters (position, force, etc.)
    5. Initialize audio in the scene and audio recording.
    6. Let the object fall. Use PyImpact to generate collisions.
    7. The trial stops either when the sound stops playing or if a maximum number of frames has been reached.
    8. Save the results to disk.

    **Result:** A directory dataset files. The dataset has a `random_seeds.npy` file that is used to select random seeds per trial.

    Each trial is saved in a `scene_layout` directory and has two files:
    
    1. A .json file of the [`Trial` data](../api/trial.md).
    2. An audio .wave file.
    
    ```
    D:/multimodal_challenge/
    ....random_seeds.npy
    ....mm_kitchen_1a_0/  # scene_layout
    ........00000.json
    ........00000.wav
    ........00001.json
    ........00001.wav
    ........(etc.)
    ....mm_kitchen_1a_1/
    ```
    """

    """:class_var
    The PyAudio object. This is used to determine when a trial ends (when the audio stops playing).
    """
    PY_AUDIO: pyaudio.PyAudio = pyaudio.PyAudio()
    """:class_var
    PyImpact initial amp value.
    """
    INITIAL_AMP: float = 0.5
    """:class_var
    The PyImpact object used to generate impact sound audio at runtime.
    """
    PY_IMPACT: PyImpact = PyImpact(initial_amp=INITIAL_AMP)
    """:class_var
    The path to the temporary audio file.
    """
    TEMP_AUDIO_PATH: Path = DATASET_DIRECTORY.joinpath("temp.wav")

    def __init__(self, port: int = 1071, random_seed: int = 0):
        """
        Create the network socket and bind the socket to the port.

        :param port: The port number.
        :param random_seed: The seed for the random number generator.
        """

        super().__init__(port=port, random_seed=random_seed, screen_height=128, screen_width=128, skip_frames=0)
        self.communicate([{"$type": "set_render_quality",
                           "render_quality": 0},
                          {"$type": "set_target_framerate",
                           "framerate": 100}])
        """:field
        The name of the next trial.
        """
        self.trial_count: int = 0
        """:field
        The name of the scene in the current trial.
        """
        self.scene: str = ""
        """:field
        The name of the layout of the current trial.
        """
        self.layout: int = -1
        """:field
        Parameters to define each trial. See: `rehearsal.py`.
        """
        self.trials: List[DatasetTrial] = list()
        """:field
        The ID of the target object in the current trial.
        """
        self.target_object_id: int = -1
        """:field
        The PyImpact audio materials used for the environment as an `EnvAudioMaterials` object.
        """
        self.env_audio_materials: Optional[EnvAudioMaterials] = None
        """:field
        A dummy object ID for the environment. This is reassigned per trial.
        """
        self.env_id: int = -1
        # The PyAudio device index.
        self._device_index: int = Dataset._get_pyaudio_device_index()
        # A list of random seeds per trial. We can use these to re-create any trial exactly the same every time,
        # which allows us to pause/resume dataset generation without inadvertantly changing it.
        self._random_seeds: np.array = np.array([])
        self._random_seed_index: int = 0

    def run(self) -> None:
        """
        Generate the entire dataset for each scene_layout combination.
        """

        random_seed_path = DATASET_DIRECTORY.joinpath("random_seeds.npy").resolve()
        if not DATASET_DIRECTORY.exists():
            DATASET_DIRECTORY.mkdir(parents=True)
        # Load existing random seeds.
        if random_seed_path.exists():
            self._random_seeds = np.load(str(random_seed_path))
        # Generate new random seeds for every trial.
        else:
            # Get the total number of trials.
            num_trials: int = 0
            for f in REHEARSAL_DIRECTORY.iterdir():
                if f.is_file() and f.suffix == ".json":
                    num_trials += len(loads(f.read_text(encoding="utf-8")))
            # Generate random seeds.
            self._random_seeds = self._rng.randint(low=0, high=2**31 - 1, size=num_trials, dtype=int)
            # Save them to disk.
            np.save(str(random_seed_path.resolve())[:-4], self._random_seeds)
        pbar = tqdm(total=len(self._random_seeds))
        scene_layouts = get_scene_layouts()
        for scene in scene_layouts:
            for layout in range(scene_layouts[scene]):
                self.do_trials(scene=scene, layout=layout, pbar=pbar)
        self.end()

    def do_trials(self, scene: str, layout: int, pbar: tqdm) -> None:
        """
        Get the cached trial initialization data for a scene_layout combination and do each trial.
        This will try to avoid overwriting existing trial results.
        This will start a thread to listen to audio on the sound card to determine if a trial is done.

        :param scene: The name of the scene.
        :param layout: The index of the furniture layout.
        :param pbar: The progress bar.
        """

        self._start_action()
        # Remember the name of the scene.
        self.scene = scene
        self.layout = layout
        output_directory = DATASET_DIRECTORY.joinpath(f"{scene}_{layout}")
        if not output_directory.exists():
            output_directory.mkdir(parents=True)

        # Get the environment audio materials.
        data = loads(ENV_AUDIO_MATERIALS_PATH.read_text(encoding="utf-8"))
        self.env_audio_materials = EnvAudioMaterials(**data[scene])
        self.trial_count: int = 0
        # Get the last trial number, to prevent overwriting files.
        for f in output_directory.iterdir():
            # Get the last trial completed.
            if f.is_file() and f.suffix == ".json":
                # Increment the random seed index.
                self._random_seed_index += 1
                # Try to get the last trial.
                self.trial_count += 1
        # Load the cached trial data.
        self.trials = [DatasetTrial(**d) for d in
                       loads(REHEARSAL_DIRECTORY.joinpath(f"{scene}_{layout}.json").read_text(encoding="utf-8"))]
        pbar.update(self.trial_count)
        # We already completed this portion of the dataset.
        if self.trial_count == len(self.trials):
            return
        try:
            # Initialize the scene and do the trial.
            pbar.set_description(f"{scene}_{layout}")
            for i in range(self.trial_count, len(self.trials)):
                self.do_trial(output_directory=output_directory)
                pbar.update(1)
        # Close the audio thread, stop fmedia, and stop the progress bar.
        finally:
            AudioUtils.stop()

    def do_trial(self, output_directory: Path) -> None:
        """
        Initialize the scene. This will add the target (dropped) object, the scene objects, and the Magnebot,
        as well as set a position, rotation, torso height, column rotation, and camera angles for the Magnebot.

        Start recording audio and let the object fall. The simulation ends when there's no more audio or
        if the simulation continued for too long.

        :param output_directory: The output directory for the trial data.
        """

        # Set the next random seed.
        self._rng = np.random.RandomState(self._random_seeds[self._random_seed_index])
        # Initialize the scene.
        self.init_scene(scene=self.scene, layout=self.layout)
        # Get the PyImpact audio materials for the floor and walls.
        floor = EnvAudioMaterials.RESONANCE_AUDIO_TO_PY_IMPACT[self.env_audio_materials.floor]
        wall = EnvAudioMaterials.RESONANCE_AUDIO_TO_PY_IMPACT[self.env_audio_materials.wall]
        # Cache the names of each object in PyImpact.
        object_names = dict()
        for object_id in self.objects_static:
            object_names[object_id] = self.objects_static[object_id].name
        for j in self.magnebot_static.joints:
            object_names[j] = self.magnebot_static.joints[j].name
        Dataset.PY_IMPACT.set_default_audio_info(object_names=object_names)
        # Assign audio properties per joint.
        for j in self.magnebot_static.joints:
            Dataset.PY_IMPACT.object_info[self.magnebot_static.joints[j].name] = ObjectInfo(
                name=self.magnebot_static.joints[j].name,
                mass=self.magnebot_static.joints[j].mass,
                amp=0.05,
                resonance=0.65,
                material=AudioMaterial.metal,
                bounciness=0.6,
                library="")
        try:
            # Start recording the audio.
            AudioUtils.start(output_path=Dataset.TEMP_AUDIO_PATH)
            # These commands must be sent here because `init_scene()` will try to make the Magnebot movable.
            # Also, we need some extra output data to handle audio recording.
            resp = self.communicate([{"$type": "send_rigidbodies",
                                      "frequency": "always"},
                                     {"$type": "set_immovable",
                                      "immovable": True},
                                     {"$type": "enable_image_sensor",
                                      "enable": False},
                                     {"$type": "send_audio_sources",
                                      "frequency": "always"}])
            done: bool = False
            below_floor = False
            num_frames: int = 0
            # Let the simulation run until there's too many frames or if there's no audio.
            while not done and num_frames < 1000:
                # Get impact sound commands.
                commands = Dataset.PY_IMPACT.get_audio_commands(resp=resp, floor=floor, wall=wall, resonance_audio=True)
                # Check if the object stopped moving (there won't be audio or collisions while it's falling).
                rigidbodies = get_data(resp=resp, d_type=Rigidbodies)
                sleeping = False
                for i in range(rigidbodies.get_num()):
                    if rigidbodies.get_id(i) == self.target_object_id:
                        sleeping = rigidbodies.get_sleeping(i)
                        break
                transforms = get_data(resp=resp, d_type=Transforms)
                # Stop if the object somehow fell below the floor.
                for i in range(transforms.get_num()):
                    if transforms.get_id(i) == self.target_object_id:
                        below_floor = transforms.get_position(i)[1] < -1
                        break
                audio = get_data(resp=resp, d_type=AudioSources)
                audio_playing = False
                for i in range(audio.get_num()):
                    if audio.get_is_playing(i):
                        audio_playing = True
                        break
                # This trial is done if the object isn't moving, there's no audio playing, and no pending collisions.
                if below_floor or (sleeping and not audio_playing and len(commands) == 0):
                    done = True
                else:
                    resp = self.communicate(commands)
                num_frames += 1
            # Resonance Audio might continue generating reverb after the AudioSource finishes.
            # So we'll listen to the system audio until we can't hear anything.
            self._listen_for_audio()
        finally:
            AudioUtils.stop()

        # Convert the current state of each object to initialization data.
        state = SceneState(resp=self.communicate([]))
        # If the object fell through the floor, snap it to floor level (y=0).
        if below_floor:
            state.object_transforms[self.target_object_id].position[1] = 0

        # Capture the state of each object.
        object_init_data: List[MultiModalObjectInitData] = list()
        target_object_index: int = -1
        for o_id in self.objects_static:
            i = MultiModalObjectInitData(name=self.objects_static[o_id].name,
                                         kinematic=self.objects_static[o_id].kinematic,
                                         position=TDWUtils.array_to_vector3(state.object_transforms[o_id].position),
                                         rotation=TDWUtils.array_to_vector4(state.object_transforms[o_id].rotation))
            # Set the target object as non-kinematic and record its index.
            if o_id == self.target_object_id:
                i.kinematic = False
                i.gravity = True
                target_object_index = len(object_init_data)
            object_init_data.append(i)
        # Create the trial.
        trial = Trial(object_init_data=object_init_data,
                      target_object_index=target_object_index,
                      magnebot_rotation=state.magnebot_transform.rotation,
                      magnebot_position=state.magnebot_transform.position)
        # Get the zero-padded filename.
        filename = get_trial_filename(self.trial_count)
        # Save the trial.
        output_directory.joinpath(f"{filename}.json").write_text(dumps(trial, cls=Encoder), encoding="utf-8")
        # Move the audio file.
        Dataset.TEMP_AUDIO_PATH.replace(output_directory.joinpath(f"{filename}.wav"))
        # Increment the trial counter and the random seed counter.
        self.trial_count += 1
        self._random_seed_index += 1

    def init_scene(self, scene: str, layout: int, room: int = None) -> ActionStatus:
        """
        Initialize the scene. Turn the Magnebot away from the object. Let the object fall.

        :param scene: The name of the scene.
        :param layout: The layout index.
        :param room: This parameter is ignored.

        :return: An `ActionStatus` (always success).
        """

        super().init_scene(scene=scene, layout=layout, room=room)
        # Get the angle to the object.
        angle = TDWUtils.get_angle_between(v1=self.state.magnebot_transform.forward,
                                           v2=TDWUtils.vector3_to_array(self.trials[self.trial_count].position) - self.
                                           state.magnebot_transform.position)
        if np.abs(angle) > 180:
            if angle > 0:
                angle -= 360
            else:
                angle += 360
        # Flip the angle and add some randomness. Then turn by the angle to look away from the object.
        angle += 180 + self._rng.uniform(-45, 45)
        # We need every frame for audio recording, but not right now, so let's speed things up.
        self._skip_frames = 10
        self.turn_by(angle=angle)
        # Stop skipping frames now that we're done turning.
        self._skip_frames = 0
        # Let the object fall and apply the cached force.
        # Listen for "stay" collision events to prevent a droning effect.
        self.objects_static[self.target_object_id].kinematic = False
        self._next_frame_commands.extend([{"$type": "set_kinematic_state",
                                           "id": self.target_object_id,
                                           "is_kinematic": False,
                                           "use_gravity": True},
                                          {"$type": "apply_force_to_object",
                                           "id": self.target_object_id,
                                           "force": self.trials[self.trial_count].force},
                                          {"$type": "send_collisions",
                                           "enter": True,
                                           "stay": True,
                                           "exit": True,
                                           "collision_types": ["obj", "env"]}])
        # Reset the modes here to discard any junk generated during setup.
        Dataset.PY_IMPACT.reset(initial_amp=Dataset.INITIAL_AMP)
        return ActionStatus.success

    def _cache_static_data(self, resp: List[bytes]) -> None:
        super()._cache_static_data(resp=resp)
        self.env_id = self.get_unique_id()

    def _get_object_init_commands(self) -> List[dict]:
        # Get the commands for the scene objects.
        commands = get_object_init_commands(scene=self.scene, layout=self.layout)
        return commands

    def _get_start_trial_commands(self) -> List[dict]:
        # Disable any graphics settings that could affect performance (because the camera is off).
        return [{"$type": "set_post_process",
                 "value": False},
                {"$type": "enable_reflection_probes",
                 "enable": False}]

    def _get_end_init_commands(self) -> List[dict]:
        # Add a reverb space and an audio sensor.
        return [{"$type": "set_reverb_space_simple",
                 "env_id": -1,
                 "reverb_floor_material": self.env_audio_materials.floor,
                 "reverb_ceiling_material": "acousticTile",
                 "reverb_front_wall_material": self.env_audio_materials.wall,
                 "reverb_back_wall_material": self.env_audio_materials.wall,
                 "reverb_left_wall_material": self.env_audio_materials.wall,
                 "reverb_right_wall_material": self.env_audio_materials.wall},
                {"$type": "add_environ_audio_sensor"}]

    def _get_magnebot_position(self) -> np.array:
        # Get all free occupancy map positions.
        occupancy_positions: List[np.array] = list()
        target_object_position = TDWUtils.vector3_to_array(self.trials[self.trial_count].init_data.position)
        # Prevent the Magnebot from spawning at edges of the occupancy map.
        spawn_map = np.zeros_like(self.occupancy_map)
        spawn_map.fill(1)
        spawn_map[self.occupancy_map == 0] = 0
        conv = np.ones((3, 3))
        spawn_map = convolve2d(spawn_map, conv, mode="same", boundary="fill")
        for ix, iy in np.ndindex(spawn_map.shape):
            if spawn_map[ix][iy] != 0:
                continue
            px, pz = self.get_occupancy_position(ix, iy)
            occupancy_positions.append(np.array([px, 0, pz]))
        # If the convolve function shrunk the occupancy map too much, just use the original occupancy map.
        if len(occupancy_positions) == 0:
            for ix, iy in np.ndindex(spawn_map.shape):
                if self.occupancy_map[ix][iy] != 0:
                    continue
                px, pz = self.get_occupancy_position(ix, iy)
                occupancy_positions.append(np.array([px, 0, pz]))
        # Sort the occupancy map positions by distance to the target object.
        occupancy_positions = list(sorted(occupancy_positions,
                                          key=lambda p: np.linalg.norm(p - target_object_position)))
        # Get the latter half of the positions (the further positions).
        occupancy_positions = occupancy_positions[int(len(occupancy_positions) / 2.0):]
        # Pick a random position.
        return occupancy_positions[self._rng.randint(0, len(occupancy_positions))]

    def _get_target_object(self) -> Optional[MultiModalObjectInitData]:
        return self.trials[self.trial_count].init_data

    def _listen_for_audio(self) -> None:
        """
        Source: https://stackoverflow.com/questions/892199/detect-record-audio-in-python

        Loop until audio stops playing.
        """

        threshold = 5
        chunk_size = 1024
        audio_format = pyaudio.paInt16
        rate = 44100
        stream = Dataset.PY_AUDIO.open(format=audio_format, channels=1, rate=rate,
                                       input=True, output=True,
                                       frames_per_buffer=chunk_size,
                                       input_device_index=self._device_index)
        audio = True
        try:
            # Periodically check to see if any audio is playing.
            while audio:
                snd_data = array('h', stream.read(chunk_size))
                audio = max(snd_data) > threshold
                sleep(0.1)
        finally:
            stream.stop_stream()
            stream.close()

    @staticmethod
    def _get_pyaudio_device_index() -> int:
        """
        Source: https://stackoverflow.com/questions/36894315/how-to-select-a-specific-input-device-with-pyaudio

        :return: The index of the system audio device in PyAudio.
        """

        info = Dataset.PY_AUDIO.get_host_api_info_by_index(0)
        num_devices = info.get('deviceCount')
        for i in range(0, num_devices):
            if Dataset.PY_AUDIO.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels') > 0:
                device_name = Dataset.PY_AUDIO.get_device_info_by_host_api_device_index(0, i).get('name')
                if "Stereo Mix" in device_name:
                    return i
        raise Exception("Couldn't find a suitable audio device!")


if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("--random_seed", type=int, default=0, help="The total number of trials.")
    args = parser.parse_args()
    dataset_generator = Dataset(random_seed=args.random_seed)
    dataset_generator.run()
