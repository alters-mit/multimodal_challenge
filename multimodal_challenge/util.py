from json import loads
from typing import List
from tdw.object_init_data import AudioInitData
from multimodal_challenge.paths import DROP_OBJECTS_PATH, OBJECT_INIT_DIRECTORY

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
