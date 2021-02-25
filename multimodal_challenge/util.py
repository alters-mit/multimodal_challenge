from json import loads
from typing import List
from tdw.object_init_data import AudioInitData
from tdw.librarian import SceneLibrarian
from multimodal_challenge.paths import DROP_OBJECTS_PATH, OBJECT_INIT_DIRECTORY, SCENE_LIBRARY_PATH, \
    ASSET_BUNDLES_DIRECTORY

# A list of the names of droppable objects.
DROP_OBJECTS = DROP_OBJECTS_PATH.read_text(encoding="utf-8").split("\n")


def get_scene_librarian() -> SceneLibrarian:
    """
    :return: The `SceneLibrarian`, which can point to local or remote asset bundles.
    """

    lib = SceneLibrarian(library=str(SCENE_LIBRARY_PATH.resolve()))
    for i in range(len(lib.records)):
        # Set all of the URLs based on the root path.
        for platform in lib.records[i].urls:
            url = str(ASSET_BUNDLES_DIRECTORY.joinpath(lib.records[i].urls[platform].replace("ROOT", "")).resolve())
            if not url.startswith("http"):
                url = "file:///" + url
            lib.records[i].urls[platform] = url
    return lib


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
