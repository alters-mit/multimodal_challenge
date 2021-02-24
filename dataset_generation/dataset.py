from time import sleep
from typing import List, Tuple, Dict, Optional
from pathlib import Path
from json import loads
from threading import Thread
from array import array
import numpy as np
import pyaudio
from tqdm import tqdm
from tdw.tdw_utils import AudioUtils, TDWUtils
from tdw.object_init_data import AudioInitData
from tdw.py_impact import PyImpact, AudioMaterial
from magnebot import Magnebot
from magnebot.scene_state import SceneState
from magnebot.scene_environment import SceneEnvironment
from multimodal_challenge.multimodal_base import MultiModalBase
from multimodal_challenge.trial import Trial
from multimodal_challenge.dataset_generation.drop import Drop
from multimodal_challenge.paths import AUDIO_DATASET_DROPS_DIRECTORY, ENV_AUDIO_MATERIALS_PATH
from multimodal_challenge.util import get_object_init_commands


class Dataset(MultiModalBase):
    """
    Generate an audio dataset from pre-calculated drop data.
    Save the results of each trial as a .json file of a `Trial` object.

    # Requirements
    
    - The `multimodal_challenge` Python module 
    - Run `rehearsal.py` to generate the initialization data
    - Audio drivers
    - [`PyAudio`](https://people.csail.mit.edu/hubert/pyaudio/) If you're using Windows and Python 3.7 or later, use a wheel from [this site](https://www.lfd.uci.edu/~gohlke/pythonlibs/) and install it via: `pip3 install path/to/the/downloaded.whl` (replace this with the actual path to the downloaded file)

    """

    """:class_var
    The PyAudio object. This is used to determine when a trial ends (when the audio stops playing).
    """
    PY_AUDIO: pyaudio.PyAudio = pyaudio.PyAudio()
    """:class_var
    True if there is currently audio playing. Don't set this value manually! It is handled in a separate thread.
    """
    AUDIO_IS_PLAYING: bool = False
    """:class_var
    If True, continue to listen to audio. Use this to stop the PyAudio thread.
    """
    LISTEN_TO_AUDIO: bool = False
    """:class_var
    The PyImpact object used to generate impact sound audio at runtime.
    """
    PY_IMPACT: PyImpact = PyImpact()
    """:class_var
    A dictionary. Key = A PyImpact `AudioMaterial`. Value = The corresponding Resonance Audio material.
    """
    PY_IMPACT_TO_RESONANCE_AUDIO: Dict[AudioMaterial, str] = {AudioMaterial.cardboard: "roughPlaster",
                                                              AudioMaterial.ceramic: "tile",
                                                              AudioMaterial.glass: "glass",
                                                              AudioMaterial.hardwood: "parquet",
                                                              AudioMaterial.metal: "metal",
                                                              AudioMaterial.wood: "wood"}

    def __init__(self, port: int = 1071, random_seed: int = 0, output_directory: str = "D:/multimodal_dataset"):
        """
        Create the network socket and bind the socket to the port.

        :param port: The port number.
        :param random_seed: The seed for the random number generator.
        """

        super().__init__(port=port, random_seed=random_seed, launch_build=False, screen_height=128, screen_width=128,
                         img_is_png=False, auto_save_images=False, skip_frames=0, debug=False)
        self.communicate([{"$type": "set_render_quality",
                           "render_quality": 0},
                          {"$type": "set_target_framerate",
                           "framerate": 60}])
        """:field
        The dataset output directory.
        """
        self.output_directory: Path = Path(output_directory)
        if not self.output_directory.exists():
            self.output_directory.mkdir(parents=True)
        """:field
        The path to the temporary audio file.
        """
        self.temp_audio_path: Path = self.output_directory.joinpath("temp.wav")
        # The name of the next trial.
        """:field
        The name of the next trial.
        """
        self.trial_count: int = 0
        for f in self.output_directory.iterdir():
            if f.is_file() and f.suffix == ".json":
                q = int(f.name.replace(f.suffix, ""))
                if q > self.trial_count:
                    self.trial_count = q
        """:field
        The name of the scene in the current trial.
        """
        self.scene: str = ""
        """:field
        The name of the layout of the current trial.
        """
        self.layout: int = -1
        """:field
        Parameters to define the drop of each trial. See: `rehearsal.py`.
        """
        self.drops: List[Drop] = list()
        """:field
        The position of the Magnebot in the current trial.
        """
        self.magnebot_position: np.array = np.array([0, 0, 0])
        """:field
        The rotation of the Magnebot in the current trial.
        """
        self.magnebot_rotation: float = -1
        """:field
        The height of the torso in the current trial.
        """
        self.torso_height: float = -1
        """:field
        The rotation of the column in the current trial.
        """
        self.torso_angle: float = -1
        """:field
        The camera pitch in the current trial.
        """
        self.camera_pitch: float = -1
        """:field
        The camera yaw in the current trial.
        """
        self.camera_yaw: float = -1
        """:field
        The ID of the target object in the current trial.
        """
        self.target_object_id: int = -1
        """:field
        Cached scale factors per objects for the current trial.
        """
        self.scale_factors: Dict[int, Dict[str, float]] = dict()
        """:field
        The PyImpact audio materials used for the environment. 
        Key = The room index. Value = A tuple: floor material; wall material.
        """
        self.env_audio_materials: Dict[int, Tuple[AudioMaterial, AudioMaterial]] = dict()
        """:field
        Environment data used for setting drop positions.
        """
        self.scene_environment: Optional[SceneEnvironment] = None
        """:field
        A dummy object ID for the environment. This is reassigned per trial.
        """
        self.env_id: int = -1

    def run(self) -> None:
        """
        Generate the entire dataset for each scene_layout combination.
        """

        data = loads(ENV_AUDIO_MATERIALS_PATH.read_text(encoding="utf-8"))
        for scene in data:
            for layout in data[scene]:
                self.do_trials(scene=scene, layout=layout)

    def do_trials(self, scene: str, layout: str) -> None:
        """
        Get the cached scenarios (drops) for a scene_layout combination and do each drop trial.
        This will try to avoid overwriting existing trial results.
        This will start a thread to listen to audio on the sound card to determine if a trial is done.

        :param scene: The name of the scene.
        :param layout: The index of the furniture layout.
        """

        # Remember the name of the scene.
        self.scene = scene
        self.layout = int(layout)

        # Get the environment audio materials.
        self.env_audio_materials.clear()
        data = loads(ENV_AUDIO_MATERIALS_PATH)
        for room in data[scene][layout]:
            self.env_audio_materials[int(room)] = (AudioMaterial[data[scene][layout][room["floor"]]],
                                                   AudioMaterial[data[scene][layout][room["wall"]]])
        self.trial_count: int = 0
        # Get the last trial number, to prevent overwriting files.
        for f in self.output_directory.iterdir():
            if f.is_file() and f.suffix == ".json":
                tc = int(f.name.replace(".json", ""))
                if tc > self.trial_count:
                    self.trial_count = tc + 1
        # We already completed this portion of the dataset.
        if self.trial_count == len(self.drops):
            return
        # Load the cached drop data.
        drops = AUDIO_DATASET_DROPS_DIRECTORY.joinpath(f"{scene}_{layout}.json").read_text(encoding="utf-8")
        self.drops = [Drop(**d) for d in drops["drops"]]
        # Create a progress bar.
        pbar = tqdm(total=len(self.drops))
        pbar.update(self.trial_count)
        # Start listening to audio on a separate thread.
        t = Thread(target=Dataset._listen_for_audio)
        t.daemon = True
        try:
            t.start()
            # Initialize the scene and do the trial.
            for i in range(self.trial_count, len(self.drops)):
                pbar.set_description(f"{scene}_{layout} {i}")
                self.do_trial()
                pbar.update(1)
        # Close the audio thread, stop fmedia, and stop the progress bar.
        finally:
            Dataset.LISTEN_TO_AUDIO = False
            AudioUtils.stop()
            pbar.close()

    def do_trial(self) -> None:
        """
        Initialize the scene. This will add the target (dropped) object, the scene objects, and the Magnebot,
        as well as set a position, rotation, torso height, column rotation, and camera angles for the Magnebot.

        Start recording audio and let the object fall. The simulation ends when there's no more audio or
        if the simulation continued for too long.
        """

        self.init_scene(scene=self.scene, layout=self.layout)
        try:
            # Start recording the audio.
            AudioUtils.start(output_path=self.temp_audio_path)
            # These commands must be sent here because `init_scene()` will try to make the Magnebot moveable.
            self._next_frame_commands.extend([{"$type": "send_rigidbodies",
                                               "frequency": "always"},
                                              {"$type": "set_immovable",
                                               "immovable": True}])
            frame: int = 0
            done: bool = False
            resp = self.communicate([])
            # Let the simulation run until there's too many frames or if there's no audio.
            while not done and frame < 1000:
                collisions, env_collisions, rigidbodies = Dataset.PY_IMPACT.get_collisions(resp=resp)
                commands = []
                # Play sounds from collisions.
                for collision in collisions:
                    if collision.get_state() == "enter" and Dataset.PY_IMPACT.is_valid_collision(
                            collision=collision):
                        o_0 = self.objects_static[collision.get_collider_id()]
                        o_1 = self.objects_static[collision.get_collidee_id()]
                        if o_0.mass < o_1.mass:
                            target = o_0
                            other = o_1
                        else:
                            target = o_1
                            other = o_0

                        # TODO target object might have different properties.
                        target_audio = Magnebot._OBJECT_AUDIO[target.name]
                        other_audio = Magnebot._OBJECT_AUDIO[other.name]
                        commands.append(Dataset.PY_IMPACT.get_impact_sound_command(collision=collision,
                                                                                   rigidbodies=rigidbodies,
                                                                                   target_id=target.object_id,
                                                                                   target_amp=target_audio.amp,
                                                                                   target_mat=target_audio.material.name,
                                                                                   other_id=other.object_id,
                                                                                   other_amp=other_audio.amp,
                                                                                   other_mat=other_audio.material.name,
                                                                                   resonance=target_audio.resonance,
                                                                                   play_audio_data=False))
                # Play sounds from collisions with the environment.
                for collision in env_collisions:
                    if collision.get_state() == "enter":
                        o = self.objects_static[collision.get_object_id()]
                        a = Magnebot._OBJECT_AUDIO[o.name]
                        room_id = -1
                        for i in range(collision.get_num_contacts()):
                            if room_id != -1:
                                break
                            cx, cy, cz = collision.get_contact_point(i)
                            room_id = self.scene_environment.get_room(x=cx, z=cz).room_id
                        # Somehow, the collision wasn't in a room. Ignore this collision.
                        if room_id == -1:
                            continue
                        # Get the correct environment material, given a) the room and b) if this is the floor or wall.
                        if collision.get_floor():
                            env_mat = self.env_audio_materials[room_id][0]
                        else:
                            env_mat = self.env_audio_materials[room_id][1]
                        commands.append(Dataset.PY_IMPACT.get_impact_sound_command(collision=collision,
                                                                                   rigidbodies=rigidbodies,
                                                                                   target_id=o.object_id,
                                                                                   target_amp=a.amp,
                                                                                   target_mat=a.material.name,
                                                                                   other_id=self.env_id,
                                                                                   other_amp=0.01,
                                                                                   other_mat=env_mat.name,
                                                                                   resonance=a.resonance,
                                                                                   play_audio_data=False))
                # Check if the object stopped moving (there won't be audio or collisions while it's falling).
                sleeping = False
                for i in range(rigidbodies.get_num()):
                    if rigidbodies.get_id(i) == self.target_object_id:
                        sleeping = rigidbodies.get_sleeping(i)
                        break
                # This trial is done if the object isn't moving, there's no audio playing, and no pending collisions.
                if sleeping and not Dataset.AUDIO_IS_PLAYING and len(commands) == 0:
                    done = True
                else:
                    resp = self.communicate(commands)
                frame += 1
        finally:
            AudioUtils.stop()

        # Convert the current state of each object to initialization data.
        state = SceneState(resp=self.communicate([]))
        object_init_data: List[AudioInitData] = list()
        for o_id in self.objects_static:
            name = self.objects_static[o_id].name
            # TODO the target object might have different data?
            o = AudioInitData(name=name,
                              audio=Magnebot._OBJECT_AUDIO[name],
                              position=TDWUtils.array_to_vector3(state.object_transforms[o_id].position),
                              rotation=TDWUtils.array_to_vector4(state.object_transforms[o_id].rotation),
                              gravity=True,
                              kinematic=self.objects_static[o_id].kinematic,
                              scale_factor=self.scale_factors[o_id])
            object_init_data.append(o)

        # Cache the result of the trial.
        ci = Trial(scene=self.scene,
                   magnebot_position=self.magnebot_position,
                   magnebot_rotation=self.magnebot_rotation,
                   torso_height=self.torso_height,
                   column_rotation=self.torso_angle,
                   camera_pitch=self.camera_pitch,
                   camera_yaw=self.camera_yaw,
                   audio=self.temp_audio_path.read_bytes(),
                   target_object=self.target_object_id,
                   object_init_data=object_init_data)
        # Remove the temp file.
        self.temp_audio_path.unlink()
        # Write the result to disk.
        ci.write(path=self.output_directory.joinpath(f"{self.trial_count}.json"))
        self.trial_count += 1

    def _cache_static_data(self, resp: List[bytes]) -> None:
        super()._cache_static_data(resp=resp)
        self.scene_environment = SceneEnvironment(resp=resp)
        num_attempts = 0

        # Get a unique env ID.
        got_env_id = False
        while not got_env_id and num_attempts < 100:
            self.env_id = self.get_unique_id()
            got_env_id = self.env_id in self.objects_static
            num_attempts += 1
        assert got_env_id, f"Failed to get an environment ID for PyImpact (this should never happen!)"

    def _get_object_init_commands(self) -> List[dict]:
        # Get the commands for the scene objects.
        commands = get_object_init_commands(scene=self.scene, layout=self.layout)
        # Append the drop object.
        self.target_object_id, object_commands = self.drops[self.trial_count].init_data.get_commands()
        # Record the scale factors.
        self.scale_factors.clear()
        for cmd in object_commands:
            if cmd["$type"] == "scale_object":
                self.scale_factors[cmd["id"]] = cmd["scale_factor"]
        commands.extend(object_commands)
        commands.append({"$type": "apply_force_to_object",
                         "id": self.target_object_id,
                         "force": self.drops[self.trial_count].force})
        return commands

    def _get_start_trial_commands(self) -> List[dict]:
        commands = [{"$type": "set_post_process",
                     "value": False},
                    {"$type": "enable_reflection_probes",
                     "enable": False},
                    {"$type": "set_immovable",
                     "immovable": True},
                    {"$type": "send_audio_sources",
                     "frequency": "never"},
                    {"$type": "send_rigidbodies",
                     "frequency": "never"},
                    {"$type": "send_environments",
                     "frequency": "once"}]
        # Add reverb spaces per room.
        for room in self.scene_environment.rooms:
            # Get the floor and wall materials and convert them from PyImpact to Resonance Audio.
            floor_material = Dataset.PY_IMPACT_TO_RESONANCE_AUDIO[AudioMaterial[
                self.env_audio_materials[room.room_id][0]]]
            wall_material = Dataset.PY_IMPACT_TO_RESONANCE_AUDIO[AudioMaterial[
                self.env_audio_materials[room.room_id][1]]]
            # Append the command.
            commands.append({"$type": "set_reverb_space_simple",
                             "env_id": room.room_id,
                             "reverb_floor_material": floor_material,
                             "reverb_ceiling_material": wall_material,
                             "reverb_front_wall_material": wall_material,
                             "reverb_back_wall_material": wall_material,
                             "reverb_left_wall_material": wall_material,
                             "reverb_right_wall_material": wall_material})
        return commands

    def _get_end_init_commands(self) -> List[dict]:
        # Add an audio sensor and turn off the image sensor.
        return [{"$type": "add_environ_audio_sensor"},
                {"$type": "enable_image_sensor",
                 "enable": True}]

    def _get_torso_height(self) -> float:
        self.torso_height = float(self._rng.random())
        return self.torso_height

    def _get_camera_rotation(self) -> Tuple[float, float]:
        # Set a random pitch and yaw.
        self.camera_pitch = float(self._rng.uniform(-Magnebot.CAMERA_RPY_CONSTRAINTS[1] / 2,
                                                    Magnebot.CAMERA_RPY_CONSTRAINTS[1] / 2))
        self.camera_yaw = float(self._rng.uniform(-Magnebot.CAMERA_RPY_CONSTRAINTS[2] / 2,
                                                  Magnebot.CAMERA_RPY_CONSTRAINTS[2] / 2))
        return self.camera_pitch, self.camera_yaw

    def _get_torso_angle(self) -> float:
        self.torso_angle = float(self._rng.uniform(-90, 90))
        return self.torso_angle

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

    @staticmethod
    def _listen_for_audio():
        """
        Source: https://stackoverflow.com/questions/892199/detect-record-audio-in-python

        Start this process in a thread to listen to the audio to determine if anything is still playing.
        """

        device_index: int = Dataset._get_pyaudio_device_index()
        threshold = 5
        chunk_size = 1024
        audio_format = pyaudio.paInt16
        rate = 44100
        stream = Dataset.PY_AUDIO.open(format=audio_format, channels=1, rate=rate,
                                       input=True, output=True,
                                       frames_per_buffer=chunk_size,
                                       input_device_index=device_index)
        Dataset.LISTEN_TO_AUDIO = True
        try:
            # Periodically check to see if any audio is playing.
            while Dataset.LISTEN_TO_AUDIO:
                snd_data = array('h', stream.read(chunk_size))
                Dataset.AUDIO_IS_PLAYING = max(snd_data) > threshold
                sleep(0.1)
        finally:
            stream.stop_stream()
            stream.close()
            print("STOPPED LISTENING TO AUDIO")


if __name__ == "__main__":
    dataset_generator = Dataset()
    dataset_generator.run()
