from json import loads
from typing import List
from os.path import join
from tdw.librarian import SceneLibrarian
from tdw.py_impact import ObjectInfo, AudioMaterial
from multimodal_challenge.paths import DROP_OBJECTS_PATH, OBJECT_INIT_DIRECTORY, SCENE_LIBRARY_PATH, \
    ASSET_BUNDLES_DIRECTORY
from multimodal_challenge.multimodal_object_init_data import MultiModalObjectInitData

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
            if "ROOT/" in lib.records[i].urls[platform]:
                url = lib.records[i].urls[platform].split("ROOT/")[1]
                url = join(ASSET_BUNDLES_DIRECTORY, url).replace("\\", "/")
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

    data = loads(OBJECT_INIT_DIRECTORY.joinpath(f"{scene}_{layout}.json").read_text(encoding="utf-8"))
    commands = list()
    for o in data:
        audio = ObjectInfo(name=o["audio"]["name"],
                           amp=o["audio"]["amp"],
                           mass=o["audio"]["mass"],
                           material=AudioMaterial[o["audio"]["material"]],
                           library="",
                           bounciness=o["audio"]["bounciness"],
                           resonance=o["audio"]["resonance"])
        commands.extend(MultiModalObjectInitData(audio=audio, gravity=o["gravity"], kinematic=o["kinematic"],
                                                 name=o["name"], position=o["position"], rotation=o["rotation"],
                                                 scale_factor=o["scale_factor"]).get_commands()[1])
    return commands
