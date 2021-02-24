from json import dumps
from base64 import b64decode
from pathlib import Path
from typing import List
import numpy as np
from tdw.object_init_data import AudioInitData
from tdw.py_impact import ObjectInfo, AudioMaterial
from multimodal_challenge.encoder import Encoder


class Trial:
    """
    Data used to initialize a trial. In a trial, the object has already been dropped and generated audio.
    This class will place the object at the position at which it stopped moving.
    It also includes the pre-recorded audio.
    """

    def __init__(self, scene: str, magnebot_position: np.array, magnebot_rotation: float, torso_height: float,
                 column_rotation: float, camera_pitch: float, camera_yaw: float, object_init_data: List[AudioInitData],
                 target_object: int, audio: bytes):
        """
        :param scene: The name of the scene.
        :param magnebot_position: The initial position of the Magnebot.
        :param magnebot_rotation: The initial rotation of the Magnebot in degrees.
        :param torso_height: The initial height of the Magnebot's torso.
        :param column_rotation: The initial rotation of the Magnebot's column.
        :param camera_pitch: The pitch of the camera in degrees.
        :param camera_yaw: The yaw of the camera in degrees.
        :param object_init_data: Initialization data for each object in the scene. Includes the target object.
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
            self.object_init_data: List[AudioInitData] = list()
            o: dict
            for o in object_init_data:
                object_info = ObjectInfo(**o["audio"])
                object_info.material = AudioMaterial[object_info.material]
                a = AudioInitData(name=o["name"], library=o["library"], scale_factor=o["scale_factor"],
                                  position=o["position"], rotation=o["rotation"], kinematic=o["kinematic"],
                                  gravity=o["gravity"], audio=object_info)
                self.object_init_data.append(a)
        else:
            self.object_init_data: List[AudioInitData] = object_init_data
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

    def write(self, path: Path) -> None:
        """
        Serialize this object into JSON and write to disk.

        :param path: The filepath.
        """

        path.write_text(dumps(self.__dict__, cls=Encoder), encoding="utf-8")
