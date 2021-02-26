from pathlib import Path
from pkg_resources import resource_filename

"""
Paths to data files in this Python module.
"""

# The path to the file describing the root directory of the asset bundles.
__ASSET_BUNDLES_CONFIG_PATH = Path.home().joinpath("multimodal_challenge/asset_bundles_path.txt")
assert __ASSET_BUNDLES_CONFIG_PATH.exists(), f"File not found: {__ASSET_BUNDLES_CONFIG_PATH} (see README)"
# The root directory of the asset bundles.
ASSET_BUNDLES_DIRECTORY = Path(__ASSET_BUNDLES_CONFIG_PATH.read_text(encoding="utf-8"))

# The path to the data files.
DATA_DIRECTORY = Path(resource_filename(__name__, "data"))
# The path to object data.
OBJECT_DATA_DIRECTORY = DATA_DIRECTORY.joinpath("objects")
# The path to the object librarian metadata.
OBJECT_LIBRARY_PATH = OBJECT_DATA_DIRECTORY.joinpath("library.json")
# The path to the list of droppable objects.
DROP_OBJECTS_PATH = OBJECT_DATA_DIRECTORY.joinpath("drop_objects.txt")
# The path to scene data.
SCENE_DATA_DIRECTORY = DATA_DIRECTORY.joinpath("scenes")
# The path to the scene librarian metadata.
SCENE_LIBRARY_PATH = SCENE_DATA_DIRECTORY.joinpath("library.json")
# The path to the expected scene_layout combinations.
SCENE_LAYOUT_PATH = SCENE_DATA_DIRECTORY.joinpath("scene_layout.csv")
# The path to the .json files containing object init data.
OBJECT_INIT_DIRECTORY = SCENE_DATA_DIRECTORY.joinpath("object_init")
# The path to the audio dataset_generation files.
AUDIO_DATASET_DIRECTORY = DATA_DIRECTORY.joinpath("dataset")
# The path to the .json files containing drop zone data.
DROP_ZONE_DIRECTORY = AUDIO_DATASET_DIRECTORY.joinpath("drop_zones")
# THe path to the audio dataset_generation drops .json files.
AUDIO_DATASET_DROPS_DIRECTORY = AUDIO_DATASET_DIRECTORY.joinpath("drops")
# The path to the environment audio materials.
ENV_AUDIO_MATERIALS_PATH = AUDIO_DATASET_DIRECTORY.joinpath("audio_materials.json")
