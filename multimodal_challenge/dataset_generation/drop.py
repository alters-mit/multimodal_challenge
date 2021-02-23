from typing import Dict
from tdw.object_init_data import AudioInitData
from tdw.py_impact import ObjectInfo, AudioMaterial


class Drop:
    """
    Parameters defining a dropped object.
    """

    def __init__(self, init_data: AudioInitData, force: Dict[str, float]):
        """
        :param init_data: An `AudioInitData` object defining how to initialize this object.
        :param force: The initial force of the object as a Vector3 dictionary.
        """

        # Load the drop parameters from a dictionary.
        if isinstance(init_data, dict):
            init_data: dict
            object_info = ObjectInfo(**init_data["audio"])
            object_info.material = AudioMaterial[object_info.material]
            """:field
            An `AudioInitData` object defining how to initialize this object.
            """
            self.init_data = AudioInitData(name=init_data["name"], library=init_data["library"],
                                           scale_factor=init_data["scale_factor"], position=init_data["position"],
                                           rotation=init_data["rotation"], kinematic=init_data["kinematic"],
                                           gravity=init_data["gravity"], audio=object_info)
        else:
            self.init_data: AudioInitData = init_data
        """:field
        The initial force of the object as a Vector3 dictionary.
        """
        self.force: Dict[str, float] = force
