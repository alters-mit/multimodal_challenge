from json import loads, dumps
from pathlib import Path
from typing import List
from argparse import ArgumentParser
from tdw.py_impact import PyImpact
from tdw.object_init_data import TransformInitData
from tdw.librarian import ModelLibrarian, SceneLibrarian
from tdw.controller import Controller
from multimodal_challenge.paths import OBJECT_INIT_DIRECTORY, OBJECT_LIBRARY_PATH, \
    SCENE_LIBRARY_PATH, KINEMATIC_OBJECTS_PATH
from multimodal_challenge.multimodal_object_init_data import MultiModalObjectInitData
from multimodal_challenge.encoder import Encoder


class InitData:
    """
    This is a backend tool for TDW  developers to convert saved [TDW commands](https://github.com/threedworld-mit/tdw/blob/master/Documentation/api/command_api.md) into [initialization instructions](../api/multimodal_object_init_data.md) and [metadata records](https://github.com/threedworld-mit/tdw/blob/master/Documentation/python/librarian/librarian.md).

    # Requirements

    - The `multimodal_challenge` Python module.
    - `~/tdw_config/scene_layout.txt` The object initialization data

    `~` is the home directory and `scene_layout` is the scene_layout combination, e.g. `mm_kitchen_1_a_0`.

    # Usage

    1. `cd dataset`
    2. `python3 init_data.py ARGUMENTS`
    3. Run build

    | Argument | Type | Description |
    | --- | --- | --- |
    | `--scene` | str | The name of the scene. |
    | `--layout` | int | The layout index. |
    | `--load_scene` | | If included, load the scene. Don't update the init data. |
    | `--occupancy_map` | str | Set how the occupancy map will be generated. `create`=Create an occupancy map from the list of commands. `update`=Update an occupancy map from existing init data (and don't overwrite that init data). `skip`=Don't modify the existing occupancy map. |
    """

    @staticmethod
    def get_commands(scene: str, layout: int) -> List[dict]:
        """
        :param scene: The name of the scene.
        :param layout: The layout index.

        :return: A list of commands to add objects to the scene.
        """

        root_dir = Path.home().joinpath(f"tdw_config")
        filename = f"{scene}_{layout}"
        # Append object init commands.
        commands = loads(root_dir.joinpath(f"{filename}.txt").read_text(encoding="utf-8"))
        for i in range(len(commands)):
            if commands[i]["$type"] == "add_object":
                commands[i]["scale_factor"] = 1
        return commands

    @staticmethod
    def get_init_data(scene: str, layout: int) -> None:
        """
        Create object initialization data.

        Update the scene and model metadata records in this repo's librarians.

        :param scene: The name of the scene.
        :param layout: The layout index.
        """

        bucket: str = "https://tdw-public.s3.amazonaws.com"
        # Update the scene library.
        scene_lib = SceneLibrarian(str(SCENE_LIBRARY_PATH.resolve()))
        record = scene_lib.get_record(scene)
        if record is None:
            scene_lib_core = SceneLibrarian()
            record = scene_lib_core.get_record(scene)
            # Adjust the record URLs.
            for platform in record.urls:
                record.urls[platform] = record.urls[platform].replace(bucket, "ROOT")
            scene_lib.add_or_update_record(record=record, overwrite=False, write=True)

        model_lib = ModelLibrarian(str(OBJECT_LIBRARY_PATH.resolve()))
        model_lib_core = ModelLibrarian()
        object_info = PyImpact.get_object_info()
        # Update the local model library.
        for name in object_info:
            record = model_lib.get_record(name)
            if record is None:
                record = model_lib_core.get_record(name)
                if record is not None:
                    # Adjust the record URLs.
                    for platform in record.urls:
                        record.urls[platform] = record.urls[platform].replace(bucket, "ROOT")
                    model_lib.add_or_update_record(record=record, overwrite=False)
        model_lib.write()
        # Remember where the local library is.
        TransformInitData.LIBRARIES[str(OBJECT_LIBRARY_PATH.resolve())] = \
            ModelLibrarian(library=str(OBJECT_LIBRARY_PATH.resolve()))

        # Replacements for unusable models.
        replacements = {"rope_table_lamp": "jug05",
                        "jigsaw_puzzle_composite": "puzzle_box_composite",
                        "salt": "pepper",
                        "rattan_basket": "basket_18inx18inx12iin_wicker"}
        # Get a list of kinematic objects.
        kinematic_objects = KINEMATIC_OBJECTS_PATH.read_text(encoding="utf-8").split("\n")
        # Get the commands.
        commands = InitData.get_commands(scene=scene, layout=layout)
        objects: List[MultiModalObjectInitData] = list()
        # Convert the commands to TransformInitData.
        i = 0
        done = False
        while not done:
            if i >= len(commands):
                break
            if commands[i]["$type"] != "add_object":
                done = True
            else:
                name = commands[i]["name"]
                if name in replacements:
                    name = replacements[name]
                if name in object_info:
                    commands[i]["scale_factor"] = 1
                    objects.append(MultiModalObjectInitData(name=name,
                                                            position=commands[i]["position"],
                                                            rotation=commands[i + 1]["rotation"],
                                                            kinematic=name in kinematic_objects))
                else:
                    print(f"Warning: no audio values for {name}")
                i += 3
        OBJECT_INIT_DIRECTORY.joinpath(f"{scene}_{layout}.json").write_text(dumps(objects, cls=Encoder, indent=2,
                                                                                  sort_keys=True))


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--scene", type=str, help="The name of the scene.")
    parser.add_argument("--layout", type=int, help="The layout number.")
    parser.add_argument("--load_scene", action="store_true", help="If included load the scene. "
                                                                  "Don't update the init data.")
    args = parser.parse_args()
    if args.load_scene:
        c = Controller(launch_build=False)
        cmds = [c.get_add_scene(scene_name=args.scene)]
        cmds.extend(InitData.get_commands(scene=args.scene, layout=args.layout))
        c.communicate(cmds)
    else:
        InitData.get_init_data(scene=args.scene, layout=args.layout)
