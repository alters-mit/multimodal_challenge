# InitData

`from dataset_generation.init_data import InitData`

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

***

#### get_commands

**`InitData.get_commands(scene, layout, drop_zones)`**

_This is a static function._


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| scene |  str |  | The name of the scene. |
| layout |  int |  | The layout index. |
| drop_zones |  bool |  | If True, append commands to show the drop zones. |

_Returns:_  A list of commands to add objects to the scene and optionally to show the drop zones.

#### get_init_data

**`InitData.get_init_data(scene, layout, occupancy_map)`**

_This is a static function._

Create object initialization data and update drop zone data.

Update the scene and model metadata records in this repo's librarians.

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| scene |  str |  | The name of the scene. |
| layout |  int |  | The layout index. |
| occupancy_map |  str |  | If True, generate an occupancy map. |

