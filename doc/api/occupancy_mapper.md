# OccupancyMapper

`from multimodal_challenge.occupancy_mapper import OccupancyMapper`

Create an occupancy map and image of a scene.

This is used by [`init_data.py`](../dataset/init_data.md).

***

#### \_\_init\_\_

**`OccupancyMapper()`**

**`OccupancyMapper(port=1071)`**

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| port |  int  | 1071 | The socket port. |

#### create

**`self.create(scene, layout, image_dir)`**

Create the following for a scene_layout:

- An occupancy map (which will be stored in this module)
- An image of the scene (stored in the documentation folder of the repo)

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| scene |  str |  | The name of the scene. |
| layout |  int |  | The layout index. |
| image_dir |  Path |  | The output directory for the image. |

#### get_scene_init_commands

**`self.get_scene_init_commands(occupancy_map)`**


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| occupancy_map |  |  | The occupancy map. |

_Returns:_  A list of all islands, i.e. continuous zones of traversability on the occupancy map.

