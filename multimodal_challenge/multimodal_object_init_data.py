from typing import Dict
from tdw.object_init_data import AudioInitData, TransformInitData
from tdw.py_impact import ObjectInfo
from tdw.librarian import ModelLibrarian, ModelRecord
from multimodal_challenge.paths import OBJECT_LIBRARY_PATH


class MultiModalObjectInitData(AudioInitData):
    """
    Object initialization data for the Multi-Modal Challenge.
    This is exactly the same as `AudioInitData` except that it will always set the library to the local library.
    """

    # Remember where the local library is.
    TransformInitData.LIBRARIES[str(OBJECT_LIBRARY_PATH.resolve())] = \
        ModelLibrarian(library=str(OBJECT_LIBRARY_PATH.resolve()))

    def __init__(self, name: str, scale_factor: Dict[str, float] = None,
                 position: Dict[str, float] = None, rotation: Dict[str, float] = None, kinematic: bool = False,
                 gravity: bool = True, audio: ObjectInfo = None):
        """
        :param name: The name of the model.
        :param scale_factor: The scale factor.
        :param position: The initial position. If None, defaults to: `{"x": 0, "y": 0, "z": 0`}.
        :param rotation: The initial rotation as Euler angles or a quaternion. If None, defaults to: `{"w": 1, "x": 0, "y": 0, "z": 0}`
        :param kinematic: If True, the object will be kinematic.
        :param gravity: If True, the object won't respond to gravity.
        :param audio: If None, derive physics data from the audio data in `PyImpact.get_object_info()` If not None, use these values instead of the default audio values.
        """

        super().__init__(name=name, scale_factor=scale_factor, position=position, rotation=rotation,
                         kinematic=kinematic, gravity=gravity, audio=audio, library="")

    def _get_record(self) -> ModelRecord:
        return TransformInitData.LIBRARIES[str(OBJECT_LIBRARY_PATH.resolve())].get_record(self.name)
