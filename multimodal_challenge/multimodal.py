from json import loads
from typing import List, Optional
import numpy as np
from tdw.object_init_data import AudioInitData
from magnebot import ActionStatus, ArmJoint
from multimodal_challenge.trial import Trial
from multimodal_challenge.multimodal_base import MultiModalBase
from multimodal_challenge.paths import DATASET_DIRECTORY
from multimodal_challenge.magnebot_init_data import MagnebotInitData


class MultiModal(MultiModalBase):
    """
    TODO ADD DESCRIPTION
    """

    def __init__(self, port: int = 1071, screen_width: int = 256, screen_height: int = 256, random_seed: int = None):
        """
        :param port: The socket port. [Read this](https://github.com/threedworld-mit/tdw/blob/master/Documentation/getting_started.md#command-line-arguments) for more information.
        :param screen_width: The width of the screen in pixels.
        :param screen_height: The height of the screen in pixels.
        :param random_seed: The seed used for random numbers. If None, this is chosen randomly.
        """

        super().__init__(port=port, screen_width=screen_width, screen_height=screen_height,
                         random_seed=random_seed, skip_frames=10)

        """:field
        The pre-recorded audio data for the current trial.
        """
        self.audio: bytes = b''
        """:field
        The ID of the target object in the current trial.
        """
        self.target_object: int = -1
        # Data used to initialize the next trial.
        self.__trial: Optional[Trial] = None

    def init_scene(self, scene: str, layout: int, trial: int = None) -> ActionStatus:
        """
        Initialize a scene from a `Trial` object located at: `dataset/scene_layout/trial.json`

        - `dataset` is defined in `config.ini` (see README)
        - `scene` is the name of the scene.
        - `layout` is the index of the layout.
        - `trial` is the name of the file, or the trial number.

        For example, if the dataset is located at `D:/multimodal_challenge/dataset`
        and you want to load trial 57 from mm_kitchen_1a, layout, 0:

        ```python
        from multimodal_challenge import MultiModal

        m = MultiModal()
        m.init_scene(scene="mm_kitchen_1a", layout=0, trial=57)
        ```

        :param scene: The name of the scene.
        :param layout: The layout index.
        :param trial: The trial number. If None, defaults to 0.

        :return: An `ActionStatus` (always success).
        """

        if trial is None:
            trial = 0

        # Load the cached initialization data from the trial.
        self.__trial: Trial = \
            Trial(**loads(DATASET_DIRECTORY.joinpath(f"{scene}_{layout}/{trial}.json").read_text(encoding="utf-8")))
        self.audio = self.__trial.audio
        self.target_object = self.__trial.target_object
        return super().init_scene(scene=self.__trial.scene, layout=layout)

    def set_torso(self, position: float, angle: float = None) -> ActionStatus:
        """
        Slide the Magnebot's torso up or down and optionally rotate it as well.

        Possible [return values](action_status.md):

        - `success`
        - `failed_to_bend` (If the torso failed to reach the target position and/or rotation)

        :param position: The target vertical position of the torso. Must >=0.6 and <=1.5
        :param angle: If not None, the target rotation of the torso in degrees. The default rotation of the torso is 0.

        :return: An `ActionStatus` indicating if the torso reached the target position.
        """

        self._start_action()
        # Clamp the position.
        if position < 0:
            position = 0
        elif position > 1:
            position = 1
        torso_max: float = 1.5
        torso_min: float = 0.6
        torso_id = self.magnebot_static.arm_joints[ArmJoint.torso]
        joint_ids = [torso_id]
        commands = [{"$type": "set_immovable",
                     "immovable": True},
                    {"$type": "set_prismatic_target",
                     "joint_id": torso_id,
                     "target": (position * (torso_max - torso_min)) + torso_max}]
        # Rotate the column.
        if angle is not None:
            column_id = self.magnebot_static.arm_joints[ArmJoint.column]
            commands.append({"$type": "set_revolute_target",
                             "joint_id": column_id,
                             "target": angle})
            joint_ids.append(column_id)
        self._next_frame_commands.extend(commands)
        status = self._do_arm_motion(joint_ids=joint_ids)
        self._end_action()
        return status

    def _get_start_trial_commands(self) -> List[dict]:
        return [{"$type": "set_aperture",
                 "aperture": 8.0},
                {"$type": "set_focus_distance",
                 "focus_distance": 2.25},
                {"$type": "set_post_exposure",
                 "post_exposure": 0.4},
                {"$type": "set_ambient_occlusion_intensity",
                 "intensity": 0.175},
                {"$type": "set_ambient_occlusion_thickness_modifier",
                 "thickness": 3.5}]

    def _get_end_init_commands(self) -> List[dict]:
        return []

    def _get_target_object(self) -> Optional[AudioInitData]:
        return None

    def _get_magnebot_init_data(self) -> MagnebotInitData:
        return self.__trial.magnebot

    def _get_object_init_commands(self) -> List[dict]:
        """
        :return: A list of commands to initialize the objects.
        """

        commands = []
        for i in self.__trial.object_init_data:
            object_id, object_commands = i.get_commands()
            commands.extend(object_commands)
        return commands

    def _get_magnebot_position(self) -> np.array:
        return self.__trial.magnebot.position

    def _set_initial_pose(self) -> None:
        # Strike a cool pose.
        self._next_frame_commands.extend(self.__trial.magnebot.get_commands())
        self._end_action()
