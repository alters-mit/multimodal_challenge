from json import loads
from typing import List, Dict
from os.path import join
from tdw.librarian import SceneLibrarian
from tdw.tdw_utils import TDWUtils
from multimodal_challenge.paths import TARGET_OBJECTS_PATH, OBJECT_INIT_DIRECTORY, SCENE_LIBRARY_PATH, \
    ASSET_BUNDLES_DIRECTORY, DROP_ZONE_DIRECTORY
from multimodal_challenge.multimodal_object_init_data import MultiModalObjectInitData
from multimodal_challenge.dataset.drop_zone import DropZone

# A list of the names of droppable objects.
DROP_OBJECTS: List[str] = TARGET_OBJECTS_PATH.read_text(encoding="utf-8").split("\n")


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

    data = loads(OBJECT_INIT_DIRECTORY.joinpath(f"{scene[:-1]}_{layout}.json").read_text(encoding="utf-8"))
    commands = list()
    for o in data:
        commands.extend(MultiModalObjectInitData(**o).get_commands()[1])
    return commands


def get_drop_zones(filename: str) -> List[DropZone]:
    """
    :param filename: The filename of the drop zone .json file.

    :return: A list of drop zones.
    """

    drop_zone_data = loads(DROP_ZONE_DIRECTORY.joinpath(filename).read_text(encoding="utf-8"))
    drop_zones: List[DropZone] = list()
    for drop_zone in drop_zone_data:
        drop_zones.append(DropZone(center=TDWUtils.vector3_to_array(drop_zone["position"]), radius=drop_zone["size"]))
    return drop_zones


def get_scene_layouts() -> Dict[str, int]:
    """
    :return: A dictionary. Key = The scene name (of the asset bundle). Value = Number of layouts available.
    """

    scene_layouts: Dict[str, int] = dict()
    for f in OBJECT_INIT_DIRECTORY.iterdir():
        # Expected: mm_kitchen_1_0.json, mm_kitchen_1_1.json, ... , mm_kitchen_2_2.json, ...
        if f.is_file() and f.suffix == ".json":
            # Expected: mm_kitchen_1_0
            s = f.name.replace(".json", "")
            # Expected: mm_kitchen_1
            shell = s[:-2]
            # Expected: 0
            layout = s[-1]
            for v in ["a", "b"]:
                # Expected: {"mm_kitchen_1a": 4}
                scene_layouts[shell + v] = int(layout) + 1
    return scene_layouts
