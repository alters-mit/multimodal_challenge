from typing import List, Tuple, Optional
from abc import ABC, abstractmethod
from tdw.tdw_utils import TDWUtils
from magnebot import Magnebot, ActionStatus, ArmJoint
from multimodal_challenge.util import get_scene_librarian
from multimodal_challenge.multimodal_object_init_data import MultiModalObjectInitData
from multimodal_challenge.magnebot_init_data import MagnebotInitData


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
        # Initialization data for the Magnebot.
        self._magnebot_init_data: Optional[MagnebotInitData] = None

    def init_scene(self, scene: str, layout: int, room: int = None) -> ActionStatus:
        self.scene_librarian = get_scene_librarian()
        # Add the scene.
        scene_record = self.scene_librarian.get_record(scene)
        commands: List[dict] = [{"$type": "add_scene",
                                 "name": scene_record.name,
                                 "url": scene_record.get_url()}]
        # Set the post-processing.
        commands.extend(self._get_start_trial_commands())
        # Initialize the objects.
        commands.extend(self._get_object_init_commands())

        # Add the target object.
        target_object: MultiModalObjectInitData = self._get_target_object()
        if target_object is not None:
            target_object_id, target_object_commands = target_object.get_commands()
            commands.extend(target_object_commands)
        # Initialize the Magnebot, the return data, etc.
        self._magnebot_init_data = self._get_magnebot_init_data()
        commands.extend(self._get_scene_init_commands(magnebot_position=TDWUtils.array_to_vector3(
            self._magnebot_init_data.position)))
        # Set the rotation of the Magnebot.
        for i in range(len(commands)):
            if commands[i]["$type"] == "add_magnebot":
                commands[i]["rotation"] = {"x": 0, "y": self._magnebot_init_data.rotation, "z": 0}
                break
        # Set the rotation of the camera.
        for angle, axis in zip([self._magnebot_init_data.camera_pitch, self._magnebot_init_data.camera_yaw],
                               ["pitch", "yaw"]):
            commands.append({"$type": "rotate_sensor_container_by",
                             "axis": axis,
                             "angle": float(angle)})
        commands.extend(self._get_end_init_commands())
        resp = self.communicate(commands)
        self._cache_static_data(resp=resp)
        # Set the initial torso and column positions.
        torso_commands, joint_ids = self._get_torso_commands(position=self._magnebot_init_data.torso_height,
                                                             angle=self._magnebot_init_data.column_angle)
        self._next_frame_commands.extend(torso_commands)
        self._do_arm_motion(joint_ids=joint_ids)
        self._end_action()
        return ActionStatus.success

    def _get_torso_commands(self, position: float, angle: float = None) -> Tuple[List[dict], List[int]]:
        """
        :param position: The target vertical position of the torso. Must be between 0 and 1, which corresponds in worldspace units to 0.3691028 and 1.23945 assuming that the Magnebot isn't on an incline and the floor's y coordinate is 0 (which it almost always is).
        :param angle: If not None, the target rotation of the torso in degrees. The default rotation of the torso is 0.

        :return: Tuple: A list of commands to set the torso; a list of object IDs (torso and maybe also the column).
        """

        # Clamp the position.
        if position < 0:
            position = 0
        elif position > 1:
            position = 1
        max_position = 1.5
        min_position = 0.6
        torso_id = self.magnebot_static.arm_joints[ArmJoint.torso]
        joint_ids = [torso_id]
        commands = [{"$type": "set_immovable",
                     "immovable": True},
                    {"$type": "set_prismatic_target",
                     "joint_id": torso_id,
                     "target": (position * (max_position - min_position)) + min_position}]
        # Rotate the column.
        if angle is not None:
            column_id = self.magnebot_static.arm_joints[ArmJoint.column]
            commands.append({"$type": "set_revolute_target",
                             "joint_id": column_id,
                             "target": angle})
            joint_ids.append(column_id)
        return commands, joint_ids

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
    def _get_magnebot_init_data(self) -> MagnebotInitData:
        """
        :return: Initialization data for the Magnebot.
        """

        raise Exception()
