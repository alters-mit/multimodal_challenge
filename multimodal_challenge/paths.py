from pathlib import Path
from pkg_resources import resource_filename
from argparse import ArgumentParser

"""
Paths to data files in this Python module.
"""

__parser = ArgumentParser()
__parser.add_argument("--asset_bundles", type=str, default="https://tdw-public.s3.amazonaws.com",
                      help="Root local directory or remote URL of scene and model asset bundles.")
__parser.add_argument("--dataset_directory", type=str, default="D:/multimodal_challenge",
                      help="Root local directory of the dataset files.")
__args, __unknown = __parser.parse_known_args()

# The root directory of the asset bundles.
ASSET_BUNDLES_DIRECTORY: str = __args.asset_bundles
if ASSET_BUNDLES_DIRECTORY.startswith("~"):
    ASSET_BUNDLES_DIRECTORY = str(Path.home().joinpath(ASSET_BUNDLES_DIRECTORY[2:]).resolve())
__data_dir = __args.dataset_directory
if __data_dir.startswith("~"):
    __data_dir = str(Path.home().joinpath(__data_dir[2:]).resolve())
# The path to where the dataset data will be generated.
DATASET_ROOT_DIRECTORY: Path = Path(__data_dir)
# The path to the rehearsal data.
REHEARSAL_DIRECTORY: Path = DATASET_ROOT_DIRECTORY.joinpath("rehearsal")
if not REHEARSAL_DIRECTORY.exists():
    REHEARSAL_DIRECTORY.mkdir(parents=True)
# The path to the audio dataset files.
DATASET_DIRECTORY = DATASET_ROOT_DIRECTORY.joinpath("dataset")

# The path to the data files.
DATA_DIRECTORY: Path = Path(resource_filename(__name__, "data"))
# The path to object data.
OBJECT_DATA_DIRECTORY = DATA_DIRECTORY.joinpath("objects")
# The path to the object librarian metadata.
OBJECT_LIBRARY_PATH = OBJECT_DATA_DIRECTORY.joinpath("library.json")
# The path to the list of droppable target objects.
TARGET_OBJECTS_PATH = OBJECT_DATA_DIRECTORY.joinpath("target_objects.txt")
# The path to the list of kinematic objects.
KINEMATIC_OBJECTS_PATH = OBJECT_DATA_DIRECTORY.joinpath("kinematic.txt")
# The path to scene data.
SCENE_DATA_DIRECTORY = DATA_DIRECTORY.joinpath("scenes")
# The path to the occupancy maps.
OCCUPANCY_MAPS_DIRECTORY = SCENE_DATA_DIRECTORY.joinpath("occupancy_maps")
# The path to the scene librarian metadata.
SCENE_LIBRARY_PATH = SCENE_DATA_DIRECTORY.joinpath("library.json")
# The path to the .json files containing object init data.
OBJECT_INIT_DIRECTORY = SCENE_DATA_DIRECTORY.joinpath("object_init")

# The path to the audio dataset files.
AUDIO_DATASET_DIRECTORY = DATA_DIRECTORY.joinpath("dataset")
# The path to the .json files containing drop zone data.
DROP_ZONE_DIRECTORY = AUDIO_DATASET_DIRECTORY.joinpath("drop_zones")
# The path to the environment audio materials.
ENV_AUDIO_MATERIALS_PATH = AUDIO_DATASET_DIRECTORY.joinpath("audio_materials.json")
