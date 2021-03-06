# InitData

`from dataset_generation.init_data import InitData`

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

***

#### get_commands

**`InitData.get_commands(scene, layout)`**

_This is a static function._


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| scene |  str |  | The name of the scene. |
| layout |  int |  | The layout index. |

_Returns:_  A list of commands to add objects to the scene.

#### get_init_data

**`InitData.get_init_data(scene, layout)`**

_This is a static function._

Create object initialization data.

Update the scene and model metadata records in this repo's librarians.

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| scene |  str |  | The name of the scene. |
| layout |  int |  | The layout index. |

