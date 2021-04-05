import re
from json import loads
from typing import List, Optional, Dict, Tuple
import numpy as np
from tdw.object_init_data import AudioInitData
from tdw.tdw_utils import QuaternionUtils
from magnebot import ActionStatus, ArmJoint, Magnebot
from multimodal_challenge.multimodal_base import MultiModalBase
from multimodal_challenge.paths import DATASET_DIRECTORY
from multimodal_challenge.util import get_trial_filename, get_scene_layouts
from multimodal_challenge.trial import Trial


class MultiModal(MultiModalBase):
    """
    Search for a dropped object in a room using the [Magnebot API](https://github.com/alters-mit/magnebot) and pre-calculated audio that was generated by a physics simulation of the falling object.

    ```python
    from multimodal_challenge.multimodal import MultiModal

    m = MultiModal()
    m.init_scene(scene="mm_kitchen_1a", layout=0, trial=57)
    ```

    Each combination of `init_scene()` parameters loads a trial. Each trial was generated by [`dataset.py`](../dataset/dataset.md).

    Per trial, the scene is initialized to be exactly as it was when the object stopped moving (after it fell).
    Each trial has audio data that was generated as the object collided with other objects and the walls and floors.

    Using its camera and the audio data, the Magnebot must find the dropped object.

    [TOC-MM]
    """

    """:class_var
    A dictionary of each scene name and the number of layouts per scene. Use this to set the `scene` and `layout` parameters of `init_scene()`.
    """
    SCENE_LAYOUTS: Dict[str, int] = get_scene_layouts()

    """:class_var
    The number of trials per scene_layout combination. Use this to set the `trial` parameter of `init_scene()`:
    """
    TRIALS_PER_SCENE_LAYOUT: int = 0
    # We assume that all of the scene_layout combinations have the same number of trials.
    for f in DATASET_DIRECTORY.joinpath("mm_craftroom_1a_0").iterdir():
        # Expected filename pattern: 00000.json, 00001.json, 00002.json, ... etc.
        if re.search(r"[0-9]{5,}\.json", f.name) is not None:
            TRIALS_PER_SCENE_LAYOUT += 1
    """:class_var
    The lower and upper limits of the torso's position from the floor (y=0), assuming that the Magnebot is level.
    """
    TORSO_LIMITS: Tuple[float, float] = (Magnebot._COLUMN_Y + Magnebot._TORSO_MIN_Y,
                                         Magnebot._COLUMN_Y + Magnebot._TORSO_MAX_Y)

    def __init__(self, port: int = 1071, screen_width: int = 256, screen_height: int = 256):
        """
        :param port: The socket port. [Read this](https://github.com/threedworld-mit/tdw/blob/master/Documentation/getting_started.md#command-line-arguments) for more information.
        :param screen_width: The width of the screen in pixels.
        :param screen_height: The height of the screen in pixels.
        """

        super().__init__(port=port, screen_width=screen_width, screen_height=screen_height, skip_frames=10)

        """:field
        The pre-recorded audio generated by the target object falling as a .wav file.
        """
        self.audio: bytes = b''
        """:field
        The ID of the target object (the object that fell).
        """
        self.target_object_id: int = -1
        # Data used to initialize the next trial.
        self.__trial: Optional[Trial] = None

    def init_scene(self, scene: str, layout: int, trial: int = None) -> ActionStatus:
        """
        **Always call this function before starting a new trial.** Initialize a scene and a furniture layout, including the target object after it has fallen.
        Load the corresponding audio that was generated by the fall (`self.fall`) and position the Magnebot in the same spot as where it was when the object fell.

        - For a dictionary of valid scene names and layout indices, see: `MultiModal.SCENE_LAYOUTS`.
        - For the total number of trials per scene_layout, see: `MultiModal.TRIALS_PER_SCENE_LAYOUT`
        - [These are images of every scene_layout combination](https://github.com/alters-mit/multimodal_challenge/tree/main/doc/images/scene_layouts)

        :param scene: The name of the scene.
        :param layout: The layout index.
        :param trial: The trial number.

        :return: An `ActionStatus` (always success).
        """

        if trial is None:
            trial = 0
        trial_filename = get_trial_filename(trial)
        self.__trial = Trial(**loads(DATASET_DIRECTORY.joinpath(f"{scene}_{layout}/{trial_filename}.json").
                                     read_text(encoding="utf-8")))
        self.audio: bytes = DATASET_DIRECTORY.joinpath(f"{scene}_{layout}/{trial_filename}.wav").read_bytes()
        # Get object initialization commands and find the target object.
        for i, init_data in enumerate(self.__trial.object_init_data):
            object_id, object_commands = init_data.get_commands()
            self._object_init_commands[object_id] = object_commands
            # Get the target object ID.
            if i == self.__trial.target_object_index:
                self.target_object_id = object_id
        # Load the scene.
        super().init_scene(scene=scene, layout=layout)
        # Turn the Magnebot. We don't want to set the rotation in case the joints intersect with something.
        angle = QuaternionUtils.get_y_angle(QuaternionUtils.IDENTITY, self.__trial.magnebot_rotation)
        self.turn_by(angle, aligned_at=0.5)
        return ActionStatus.success

    def set_torso(self, position: float) -> ActionStatus:
        """
        Slide the Magnebot's torso up or down.

        The torso's position will be reset the next time the Magnebot moves or turns.

        Possible return values:

        - `success`
        - `failed_to_bend` (If the torso failed to reach the target position)

        :param position: The target vertical position of the torso. This is clamped to be within the torso limits (see: `MultiModal.TORSO_LIMITS`).

        :return: An `ActionStatus` indicating if the torso reached the target position.
        """

        self._start_action()

        # Clamp the `position` to be within the torso position limits.
        position = max(min(position, MultiModal.TORSO_LIMITS[1]), MultiModal.TORSO_LIMITS[0])
        # Convert `position` to a prismatic joint position.
        position = self._y_position_to_torso_position(position)
        # Send the command and wait for the action to finish.
        self._next_frame_commands.extend([{"$type": "set_immovable",
                                           "immovable": True},
                                          {"$type": "set_prismatic_target",
                                           "joint_id": self.magnebot_static.arm_joints[ArmJoint.torso],
                                           "target": position}])
        status = self._do_arm_motion(joint_ids=[self.magnebot_static.arm_joints[ArmJoint.torso]])
        self._end_action()
        return status

    def _get_target_object(self) -> Optional[AudioInitData]:
        return None

    def _get_magnebot_position(self) -> np.array:
        return self.__trial.magnebot_position

    def _get_end_commands(self) -> List[dict]:
        return []
