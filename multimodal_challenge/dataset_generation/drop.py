from typing import Dict
from tdw.py_impact import ObjectInfo, AudioMaterial
from multimodal_challenge.multimodal_object_init_data import MultiModalObjectInitData


class Drop:
    """
    Parameters for defining a dropped object: its starting position, rotation, etc. plus a force vector.
    """

    def __init__(self, init_data: MultiModalObjectInitData, force: Dict[str, float]):
        """
        :param init_data: A [`MultiModalObjectInitData` object](multimodal_object_init_data.md).
        :param force: The initial force of the object as a Vector3 dictionary.
        """

        # Load the drop parameters from a dictionary.
        if isinstance(init_data, dict):
            init_data: dict
            object_info = ObjectInfo(**init_data["audio"])
            object_info.material = AudioMaterial[object_info.material]
            """:field
            An [`MultiModalObjectInitData` object](multimodal_object_init_data.md).
            """
            self.init_data = MultiModalObjectInitData(name=init_data["name"], scale_factor=init_data["scale_factor"],
                                                      position=init_data["position"], rotation=init_data["rotation"],
                                                      kinematic=init_data["kinematic"], gravity=init_data["gravity"],
                                                      audio=object_info)
        else:
            self.init_data: MultiModalObjectInitData = init_data
        """:field
        The initial force of the object as a Vector3 dictionary.
        """
        self.force: Dict[str, float] = force
