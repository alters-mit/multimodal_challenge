from typing import Dict
from tdw.py_impact import AudioMaterial


class EnvAudioMaterials:
    """
    PyImpact and Resonance Audio materials for the floor and walls of a scene.
    """

    """:class_var
    A dictionary. Key = A PyImpact `AudioMaterial`. Value = The corresponding Resonance Audio material.
    """
    PY_IMPACT_TO_RESONANCE_AUDIO: Dict[AudioMaterial, str] = {AudioMaterial.cardboard: "roughPlaster",
                                                              AudioMaterial.ceramic: "tile",
                                                              AudioMaterial.glass: "glass",
                                                              AudioMaterial.hardwood: "parquet",
                                                              AudioMaterial.metal: "metal",
                                                              AudioMaterial.wood: "wood"}

    def __init__(self, floor: str, wall: str):
        """
        :param floor: The PyImpact floor audio material as a string.
        :param wall: The PyImpact wall audio material as a string.
        """

        """:field
        The PyImpact floor floor material.
        """
        self.floor: AudioMaterial = AudioMaterial[floor]
        """:field
        The PyImpact wall audio material.
        """
        self.wall: AudioMaterial = AudioMaterial[wall]
