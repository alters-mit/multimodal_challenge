import re
from json import loads
from typing import List, Optional, Dict
import numpy as np
from tdw.object_init_data import AudioInitData
from tdw.tdw_utils import TDWUtils
from magnebot import ActionStatus, ArmJoint
from multimodal_challenge.trial import Trial
from multimodal_challenge.multimodal_base import MultiModalBase
from multimodal_challenge.paths import DATASET_DIRECTORY
from multimodal_challenge.magnebot_init_data import MagnebotInitData
from multimodal_challenge.util import get_trial_filename, get_scene_layouts


class MultiModal(MultiModalBase):
    """
    Search for a dropped object in a room using the [Magnebot API](https://github.com/alters-mit/magnebot) and pre-calculated audio that was generated by a physics simulation of the falling object.

    ```python
    from multimodal_challenge import MultiModal

    m = MultiModal()
    m.init_scene(scene="mm_kitchen_1a", layout=0, trial=57)
    ```

    Each combination of `init_scene()` parameters loads a trial. Each trial was generated by [`dataset.py`](../dataset/dataset.md).

    Per trial, the scene is initialized to be exactly as it was when the object stopped moving (after it fell).
    Each trial has audio data that was generated as the object collided with other objects and the walls and floors.

    Using its camera and the audio data, the Magnebot must find the dropped object.

    [TOC]

    ## The target object

    By default, the Magnebot API records the position of every object in the scene as well as images, the position of the Magnebot, etc. See [`self.state`](https://github.com/alters-mit/magnebot/blob/main/doc/api/scene_state.md)

    In the MultiModal API, the ID of the target object is stored as `self.target_object_id`. You can use this ID to verify that the Magnebot successfully found the target object.

    ```python
    from multimodal_challenge import MultiModal

    m = MultiModal()
    m.init_scene(scene="mm_kitchen_1a", layout=0, trial=57)

    if m.target_object_id in m.get_visible_objects():
        print("Magnebot can see the target object.")

    target_object_transform = m.state.object_transforms[m.target_object_id]
    print(target_object_transform.position)
    ```
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
    for f in DATASET_DIRECTORY.joinpath("mm_kitchen_1a_0").iterdir():
        # Expected filename pattern: 00000.json, 00001.json, 00002.json, ... etc.
        if re.search(r"[0-9]{5,}\.json", f.name) is not None:
            TRIALS_PER_SCENE_LAYOUT += 1

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
        **Always call this function before starting a new trial.**

        Initialize a scene and a furniture layout, including the target object after it has fallen.
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
        filename = get_trial_filename(trial)
        # Load the cached initialization data from the trial.
        self.__trial: Trial = \
            Trial(**loads(DATASET_DIRECTORY.joinpath(f"{scene}_{layout}/{filename}.json").read_text(encoding="utf-8")))

        self.audio: bytes = DATASET_DIRECTORY.joinpath(f"{scene}_{layout}/{filename}.wav").read_bytes()
        # Load the scene.
        super().init_scene(scene=self.__trial.scene, layout=layout)
        for i, object_id in enumerate(self.objects_static):
            if i == self.__trial.target_object_index:
                self.target_object_id: int = object_id
                break
        return ActionStatus.success

    def set_torso(self, position: float, angle: float = None) -> ActionStatus:
        """
        Slide the Magnebot's torso up or down and optionally rotate it as well.

        The torso's position and angle will be reset the next time the Magnebot moves or turns.

        Possible return values:

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
                     "target": (position * (torso_max - torso_min)) + torso_min}]
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

    def _get_scene_init_commands(self, magnebot_position: Dict[str, float] = None) -> List[dict]:
        commands = super()._get_scene_init_commands(magnebot_position=magnebot_position)
        # Set the initial rotation of the Magnebot.
        commands.append({"$type": "teleport_robot",
                         "position": magnebot_position,
                         "rotation": TDWUtils.array_to_vector4(self.__trial.magnebot.rotation)})
        return commands

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
