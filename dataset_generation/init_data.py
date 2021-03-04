from json import loads, dumps
from pathlib import Path
from typing import List
from argparse import ArgumentParser
from tdw.py_impact import PyImpact
from tdw.librarian import ModelLibrarian, SceneLibrarian
from tdw.controller import Controller
from multimodal_challenge.paths import DROP_ZONE_DIRECTORY, OBJECT_INIT_DIRECTORY, OBJECT_LIBRARY_PATH, \
    SCENE_LIBRARY_PATH, TARGET_OBJECTS_PATH
from multimodal_challenge.multimodal_object_init_data import MultiModalObjectInitData
from multimodal_challenge.encoder import Encoder
from multimodal_challenge.occupancy_mapper import OccupancyMapper


class InitData:
    """
    This is a backend tool for TDW  developers to convert saved [TDW commands](https://github.com/threedworld-mit/tdw/blob/master/Documentation/api/command_api.md) into [initialization instructions](../api/multimodal_object_init_data.md) and [metadata records](https://github.com/threedworld-mit/tdw/blob/master/Documentation/python/librarian/librarian.md).

    # Requirements

    - The `multimodal_challenge` Python module.
    - Two files of initialization data:
        - `~/tdw_config/scene_layout.txt` The object initialization data
        - `~/tdw_config/scene_layout.json` The drop zone data

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
    | `--drop_zones` | | If included, show the drop zones. Ignored unless there is a `--load_scene` flag present. |
    | `--occupancy_map` | str | Set how the occupancy map will be generated. `create`=Create an occupancy map from the list of commands. `update`=Update an occupancy map from existing init data (and don't overwrite that init data). `skip`=Don't modify the existing occupancy map. |
    """

    @staticmethod
    def get_commands(scene: str, layout: int, drop_zones: bool) -> List[dict]:
        """
        :param scene: The name of the scene.
        :param layout: The layout index.
        :param drop_zones: If True, append commands to show the drop zones.

        :return: A list of commands to add objects to the scene and optionally to show the drop zones.
        """

        root_dir = Path.home().joinpath("tdw_config")
        filename = f"{scene}_{layout}"
        # Append object init commands.
        commands = loads(root_dir.joinpath(f"{filename}.txt").read_text(encoding="utf-8"))
        # Update the drop zone data.
        drop_zone_src = root_dir.joinpath(f"{filename}.json")
        drop_zone_dst = DROP_ZONE_DIRECTORY.joinpath(f"{filename}.json")
        drop_zone_data = loads(drop_zone_src.read_text(encoding="utf-8"))
        drop_zone_dst.write_text(dumps(drop_zone_data["position_markers"]), encoding="utf-8")
        # Show the drop zones.
        if drop_zones:
            dzs = loads(drop_zone_dst.read_text(encoding="utf-8"))
            for dz in dzs:
                commands.append({"$type": "add_position_marker",
                                 "position": dz["position"],
                                 "shape": "circle",
                                 "scale": dz["size"]})
            commands.append({"$type": "set_floorplan_roof",
                             "show": False})
        return commands

    @staticmethod
    def get_init_data(scene: str, layout: int, occupancy_map: str) -> None:
        """
        Create object initialization data and update drop zone data.

        Update the scene and model metadata records in this repo's librarians.

        :param scene: The name of the scene.
        :param layout: The layout index.
        :param occupancy_map: If True, generate an occupancy map.
        """

        # Update an occupancy map.
        if occupancy_map == "update":
            m = OccupancyMapper()
            m.create(scene=scene, layout=layout, image_dir=Path("../doc/images"))
            return

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

        object_info = PyImpact.get_object_info()
        # Replacements for unusable models.
        replacements = {"rope_table_lamp": "jug05",
                        "jigsaw_puzzle_composite": "puzzle_box_composite",
                        "salt": "pepper",
                        "rattan_basket": "basket_18inx18inx12iin_bamboo"}
        # Get the commands.
        commands = InitData.get_commands(scene=scene, layout=layout, drop_zones=False)
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
                # Get the objects that are hanging from the wall and make them kinematic.
                if "cabinet" in name or "painting" in name or "_rug" in name or "fridge" in name \
                        or name == "fruit_basket" or "floor_lamp" in name:
                    kinematic = True
                else:
                    kinematic = False
                if name in object_info:
                    objects.append(MultiModalObjectInitData(name=name,
                                                            position=commands[i]["position"],
                                                            rotation=commands[i + 1]["rotation"],
                                                            kinematic=kinematic))
                else:
                    print(f"Warning: no audio values for {name}")
                i += 3
        OBJECT_INIT_DIRECTORY.joinpath(f"{scene}_{layout}.json").write_text(dumps(objects, cls=Encoder, indent=2,
                                                                                  sort_keys=True))
        # Update the library.
        model_lib = ModelLibrarian(str(OBJECT_LIBRARY_PATH.resolve()))
        model_lib_core = ModelLibrarian()
        model_names = [o.name for o in objects]
        # Get the drop objects.
        model_names.extend(TARGET_OBJECTS_PATH.read_text(encoding="utf-8").split("\n"))
        model_names = list(sorted(model_names))
        for o in model_names:
            record = model_lib.get_record(o)
            if record is None:
                record = model_lib_core.get_record(o)
                # Adjust the record URLs.
                for platform in record.urls:
                    record.urls[platform] = record.urls[platform].replace(bucket, "ROOT")
                model_lib.add_or_update_record(record=record, overwrite=False)
        model_lib.write()

        # Generate an occupancy map.
        if occupancy_map == "create":
            m = OccupancyMapper()
            m.create(scene=scene, layout=layout, image_dir=Path("../doc/images"))
        return


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--scene", type=str, help="The name of the scene.")
    parser.add_argument("--layout", type=int, help="The layout number.")
    parser.add_argument("--load_scene", action="store_true", help="If included load the scene. "
                                                                  "Don't update the init data.")
    parser.add_argument("--drop_zones", action="store_true", help="If included, show the drop zones. Ignored unless "
                                                                  "there is a `--load_scene` flag present.")
    parser.add_argument("--occupancy_map", type=str, choices=["create", "update", "skip"], default="create",
                        help="Create an occupancy map. "
                             "create=Create a new occupancy map. "
                             "update=Use existing init data to update an occupancy map. "
                             "skip=Don't create an occupancy map.")
    args = parser.parse_args()
    if args.load_scene:
        c = Controller(launch_build=False)
        cmds = [c.get_add_scene(scene_name=args.scene)]
        cmds.extend(InitData.get_commands(scene=args.scene, layout=args.layout,
                                          drop_zones=args.drop_zones is not None))
        c.communicate(cmds)
    else:
        InitData.get_init_data(scene=args.scene, layout=args.layout, occupancy_map=args.occupancy_map)
