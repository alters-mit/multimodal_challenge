from typing import List, Optional
from json import loads
from abc import ABC, abstractmethod
import numpy as np
from tdw.tdw_utils import TDWUtils
from magnebot import Magnebot, ActionStatus
from multimodal_challenge.util import get_scene_librarian
from multimodal_challenge.multimodal_object_init_data import MultiModalObjectInitData
from multimodal_challenge.paths import OCCUPANCY_MAPS_DIRECTORY, SCENE_BOUNDS_DIRECTORY


class MultiModalBase(Magnebot, ABC):
    def __init__(self, port: int = 1071, screen_width: int = 256, screen_height: int = 256, random_seed: int = None,
                 skip_frames: int = 10):
        """
        :param port: The socket port. [Read this](https://github.com/threedworld-mit/tdw/blob/master/Documentation/getting_started.md#command-line-arguments) for more information.
        :param screen_width: The width of the screen in pixels.
        :param screen_height: The height of the screen in pixels.
        :param random_seed: The seed used for random numbers. If None, this is chosen randomly. In the Magnebot API this is used only when randomly selecting a start position for the Magnebot (see the `room` parameter of `init_scene()`). The same random seed is used in higher-level APIs such as the Transport Challenge.
        :param skip_frames: The build will return output data this many physics frames per simulation frame (`communicate()` call). This will greatly speed up the simulation, but eventually there will be a noticeable loss in physics accuracy. If you want to render every frame, set this to 0.
        """

        super().__init__(port=port, launch_build=False, screen_width=screen_width, screen_height=screen_height,
                         auto_save_images=False, random_seed=random_seed, img_is_png=False, skip_frames=skip_frames)
        """:field
        The ID of the target object.
        """
        self.target_object_id: int = -1

    def init_scene(self, scene: str, layout: int, room: int = None) -> ActionStatus:
        self.scene_librarian = get_scene_librarian()
        # Add the scene.
        scene_record = self.scene_librarian.get_record(scene)
        commands: List[dict] = [{"$type": "add_scene",
                                 "name": scene_record.name,
                                 "url": scene_record.get_url()}]
        self.occupancy_map = np.load(str(OCCUPANCY_MAPS_DIRECTORY.joinpath(f"{scene}_{layout}.npy").resolve()))
        self._scene_bounds = loads(SCENE_BOUNDS_DIRECTORY.joinpath(f"{scene}_{layout}.json").read_text())
        # Set the post-processing.
        commands.extend(self._get_start_trial_commands())
        # Initialize the objects.
        commands.extend(self._get_object_init_commands())

        # Add the target object.
        target_object: MultiModalObjectInitData = self._get_target_object()
        if target_object is not None:
            self.target_object_id, target_object_commands = target_object.get_commands()
            commands.extend(target_object_commands)
        commands.extend(self._get_scene_init_commands(magnebot_position=TDWUtils.array_to_vector3(
            self._get_magnebot_position())))
        commands.extend(self._get_end_init_commands())
        resp = self.communicate(commands)
        self._cache_static_data(resp=resp)
        self._end_action()
        self._set_initial_pose()
        return ActionStatus.success

    @abstractmethod
    def _get_start_trial_commands(self) -> List[dict]:
        """
        :return: Commands to send at the start of trial initialization.
        """

        raise Exception()

    @abstractmethod
    def _get_end_init_commands(self) -> List[dict]:
        """
        :return: Commands to send at the end of trial initialization but before setting the torso position and angle.
        """

        raise Exception()

    @abstractmethod
    def _get_object_init_commands(self) -> List[dict]:
        """
        :return: A list of commands to initialize the objects.
        """

        raise Exception()

    @abstractmethod
    def _get_target_object(self) -> Optional[MultiModalObjectInitData]:
        """
        :return: Object initialization data for the target object.
        """

        raise Exception()

    @abstractmethod
    def _get_magnebot_position(self) -> np.array:
        """
        :return: The initial position of the Magnebot.
        """

        raise Exception()

    @abstractmethod
    def _set_initial_pose(self) -> None:
        """
        Set the initial pose of the Magnebot.
        """

        raise Exception()
