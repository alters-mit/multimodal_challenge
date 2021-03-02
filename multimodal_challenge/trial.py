from base64 import b64decode
from typing import List
from multimodal_challenge.multimodal_object_init_data import MultiModalObjectInitData
from multimodal_challenge.magnebot_init_data import MagnebotInitData


class Trial:
    """
    Data used to initialize a trial. In a trial, the object has already been dropped and generated audio.
    This class will place the object at the position at which it stopped moving.
    It also includes the pre-recorded audio.
    """

    def __init__(self, scene: str, magnebot: MagnebotInitData, object_init_data: List[MultiModalObjectInitData],
                 target_object: int, audio: bytes):
        """
        :param scene: The name of the scene.
        :param magnebot: [Initialization data for the Magnebot](magnebot_init_data.md).
        :param object_init_data: [Initialization data](multimodal_object_init_data.md) for each object in the scene.
        :param target_object: The ID of the target object.
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
        [Initialization data for the Magnebot](magnebot_init_data.md).
        """
        self.magnebot: MagnebotInitData = magnebot
        """:field
        The ID of the target object.
        """
        self.target_object: int = target_object
        if isinstance(audio, str):
            """:field
            The audio that was recorded while the object was moving.
            """
            self.audio: bytes = b64decode(audio)
        else:
            self.audio: bytes = audio
