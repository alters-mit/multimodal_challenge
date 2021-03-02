# OccupancyMapper

`from dataset_generation.occupancy_mapper import OccupancyMapper`

Create the occupancy maps and images of scenes.

***

#### get_islands

**`OccupancyMapper(FloorplanController).get_islands(occupancy_map)`**

_This is a static function._


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| occupancy_map |  np.array |  | The occupancy map. |

_Returns:_  A list of all islands, i.e. continuous zones of traversability on the occupancy map.

#### get_island

**`OccupancyMapper(FloorplanController).get_island(occupancy_map, p)`**

_This is a static function._

Fill the island (a continuous zone) that position `p` belongs to.


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| occupancy_map |  np.array |  | The occupancy map. |
| p |  np.array |  | The position. |

_Returns:_  An island of positions as a list of (x, z) tuples.

#### get_occupancy_position

**`OccupancyMapper(FloorplanController).get_occupancy_position(scene_env, ix, iy)`**

_This is a static function._

Convert an occupancy map position to a worldspace position.



| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| scene_env |  SceneEnvironment |  | The scene environment. |
| ix |  int |  | The x coordinate of the occupancy map position. |
| iy |  int |  | The y coordinate of the occupancy map position. |

_Returns:_  The `(x, z)` position in worldspace corresponding to `(ix, iy`) on the occupancy map.

#### create

**`self.create()`**

Create the following:

- Occupancy maps as numpy arrays.
- Images of each occupancy map with markers showing which positions are navigable.
- Images of each scene+layout combination.
- Images of where the rooms are in a scene.
- Spawn position data as a json file.

#### get_scene_init_commands

**`self.get_scene_init_commands()`**

