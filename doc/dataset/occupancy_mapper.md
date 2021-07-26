# OccupancyMapper

`from dataset_generation.occupancy_mapper import OccupancyMapper`

For each scene_layout combination, create occupancy maps for object placement and for spawning the Magnebot.
Verify that there are enough valid places for the Magnebot and objects.

***

#### \_\_init\_\_

**`OccupancyMapper(scene, layout)`**

Create occupancy maps for a scene_layout combination.

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| scene |  |  | The scene name. |
| layout |  |  | The layout index. |

#### create

**`self.create(scene, layout)`**

Create occupancy maps for a scene_layout combination.

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| scene |  str |  | The scene name. |
| layout |  int |  | The layout index. |

#### run

**`self.run()`**

Create occupancy maps for each scene_layout combination.

