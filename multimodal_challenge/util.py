from json import loads
from typing import List, Dict, Tuple
from tdw.object_init_data import AudioInitData
from tdw.py_impact import AudioMaterial
from multimodal_challenge.paths import DROP_OBJECTS_PATH, OBJECT_INIT_DIRECTORY, ENV_AUDIO_MATERIALS_PATH

# Translate PyImpact audio materials to Resonance Audio materials.
PY_IMPACT_TO_RESONANCE_AUDIO: Dict[AudioMaterial, str] = {AudioMaterial.cardboard: "roughPlaster",
                                                          AudioMaterial.ceramic: "tile",
                                                          AudioMaterial.glass: "glass",
                                                          AudioMaterial.hardwood: "parquet",
                                                          AudioMaterial.metal: "metal",
                                                          AudioMaterial.wood: "wood"}

# A list of the names of droppable objects.
DROP_OBJECTS = DROP_OBJECTS_PATH.read_text(encoding="utf-8").split("\n")


def get_object_init_commands(scene: str, layout: int) -> List[dict]:
    """
    :param scene: The name of the scene.
    :param layout: The layout variant.

    :return: A list of commands to instantiate objects.
    """

    data = loads(OBJECT_INIT_DIRECTORY.joinpath(f"{scene}_{layout}.json"))
    commands = list()
    for o in data["objects"]:
        commands.extend(AudioInitData(**o).get_commands()[1])
    return commands


def get_env_audio_materials(scene: str, layout: int) -> Tuple[AudioMaterial, AudioMaterial]:
    """
    :param scene: The name of the scene.
    :param layout: The layout variant.

    :return: Tuple: The floor material; the wall material.
    """

    data = loads(ENV_AUDIO_MATERIALS_PATH.joinpath(f"{scene}_{layout}.json"))
    return AudioMaterial[data[scene][layout]["floor"]], AudioMaterial[data[scene][layout]["wall"]]
