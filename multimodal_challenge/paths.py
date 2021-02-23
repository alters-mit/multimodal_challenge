from pathlib import Path
from pkg_resources import resource_filename

"""
Paths to data files in this Python module.
"""

# The path to the data files.
DATA_DIRECTORY = Path(resource_filename(__name__, "data"))
# The path to object data.
OBJECT_DATA_DIRECTORY = DATA_DIRECTORY.joinpath("objects")
# The path to the list of droppable objects.
DROP_OBJECTS_PATH = OBJECT_DATA_DIRECTORY.joinpath("drop_objects.txt")
# The path to scene data.
SCENE_DATA_DIRECTORY = DATA_DIRECTORY.joinpath("scenes")
# The path to the .json files containing object init data.
OBJECT_INIT_DIRECTORY = SCENE_DATA_DIRECTORY.joinpath("object_init")
# The path to the .json files containing drop zone data.
DROP_ZONE_DIRECTORY = SCENE_DATA_DIRECTORY.joinpath("drop_zones")
# The path to the audio dataset files.
AUDIO_DATASET_DIRECTORY = DATA_DIRECTORY.joinpath("audio_dataset")
# THe path to the audio dataset drops .json files.
AUDIO_DATASET_DROPS_DIRECTORY = AUDIO_DATASET_DIRECTORY.joinpath("drops")
