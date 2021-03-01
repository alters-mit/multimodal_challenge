from base64 import b64decode
from typing import List
import numpy as np
from multimodal_challenge.multimodal_object_init_data import MultiModalObjectInitData


class Trial:
    """
    Data used to initialize a trial. In a trial, the object has already been dropped and generated audio.
    This class will place the object at the position at which it stopped moving.
    It also includes the pre-recorded audio.
    """

    def __init__(self, scene: str, magnebot_position: np.array, magnebot_rotation: float, torso_height: float,
                 column_rotation: float, camera_pitch: float, camera_yaw: float,
                 object_init_data: List[MultiModalObjectInitData], target_object: int, audio: bytes):
        """
        :param scene: The name of the scene.
        :param magnebot_position: The initial position of the Magnebot as an `[x, y, z]` numpy array.
        :param magnebot_rotation: The initial rotation of the Magnebot in degrees.
        :param torso_height: The initial height of the Magnebot's torso.
        :param column_rotation: The initial rotation of the Magnebot's column.
        :param camera_pitch: The pitch of the camera in degrees.
        :param camera_yaw: The yaw of the camera in degrees.
        :param object_init_data: [Initialization data](multimodal_object_init_data.md) for each object in the scene. Includes the target object.
        :param target_object: The object ID of the target object.
        :param audio: The audio that was recorded while the object was moving.
        """

        """:field
        The name of the scene.
        """
        self.scene: str = scene

        if isinstance(object_init_data[0], dict):
            """:field
            Initialization data for each object in the scene. Includes the target object.
            """
            self.object_init_data: List[MultiModalObjectInitData] = list()
            o: dict
            for o in object_init_data:
                a = MultiModalObjectInitData(**o)
                self.object_init_data.append(a)
        else:
            self.object_init_data: List[MultiModalObjectInitData] = object_init_data
        """:field
        The initial position of the Magnebot.
        """
        self.magnebot_position: np.array = np.array(magnebot_position)
        """:field
        The initial rotation of the Magnebot in degrees.
        """
        self.magnebot_rotation: float = magnebot_rotation
        """:field
        The initial height of the Magnebot's torso.
        """
        self.torso_height: float = torso_height
        """:field
        The initial rotation of the Magnebot's column.
        """
        self.column_rotation: float = column_rotation
        """:field
        The pitch of the camera in degrees.
        """
        self.camera_pitch: float = camera_pitch
        """:field
        The yaw of the camera in degrees.
        """
        self.camera_yaw: float = camera_yaw
        """:field
        The object ID of the target object.
        """
        self.target_object: int = target_object
        if isinstance(audio, str):
            """:field
            The audio that was recorded while the object was moving.
            """
            self.audio: bytes = b64decode(audio)
        else:
            self.audio: bytes = audio
