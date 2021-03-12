# MultiModal

`from multimodal_challenge import MultiModal`

TODO ADD DESCRIPTION

- [Frames](#Frames)
- [Parameter types](#Parameter types)
- [Class Variables](#Class Variables)
- [Functions](#Functions)
  - [\_\_init\_\_](#\_\_init\_\_)
  - [init_scene](#init_scene)
  - [turn_by](#turn_by)
  - [turn_to](#turn_to)
  - [move_by](#move_by)
  - [move_to](#move_to)
  - [set_torso](#set_torso)


***

## Frames

Every action advances the simulation by 1 or more _simulation frames_. This occurs every time the `communicate()` function is called (which all actions call internally).

Every simulation frame advances the simulation by contains `1 + n` _physics frames_. `n` is defined in the `skip_frames` parameter of the Magnebot constructor. This greatly increases the speed of the simulation.

Unless otherwise stated, "frame" in the Magnebot API documentation always refers to a simulation frame rather than a physics frame.

***

## Parameter types

The types `Dict`, `Union`, and `List` are in the [`typing` module](https://docs.python.org/3/library/typing.html).

#### Dict[str, float]

Parameters of type `Dict[str, float]` are Vector3 dictionaries formatted like this:

```json
{"x": -0.2, "y": 0.21, "z": 0.385}
```

`y` is the up direction.

To convert from or to a numpy array:


#### Union[Dict[str, float], int]]

Parameters of type `Union[Dict[str, float], int]]` can be either a Vector3 or an integer (an object ID).

#### Arm

All parameters of type `Arm` require you to import the [Arm enum class](https://github.com/alters-mit/magnebot/blob/main/doc/api/arm.md):


***

## Class Variables

| Variable | Type | Description |
| --- | --- | --- |
| `CAMERA_RPY_CONSTRAINTS` | List[float] | The camera roll, pitch, yaw constraints in degrees. |

***


## Fields

- `audio` The pre-recorded audio data for the current trial.


- `state` [Dynamic data for all of the most recent frame after doing an action.](https://github.com/alters-mit/magnebot/blob/main/doc/api/scene_state.md) This includes image data, physics metadata, etc.       


- `auto_save_images` If True, automatically save images to `images_directory` at the end of every action.

- `images_directory` The output directory for images if `auto_save_images == True`. This is a [`Path` object from `pathlib`](https://docs.python.org/3/library/pathlib.html).

- `camera_rpy` The current (roll, pitch, yaw) angles of the Magnebot's camera in degrees as a numpy array. This is handled outside of `self.state` because it isn't calculated using output data from the build. See: `Magnebot.CAMERA_RPY_CONSTRAINTS` and `self.rotate_camera()`

- `colliding_objects` A list of objects that the Magnebot is currently colliding with.

- `colliding_with_wall` If True, the Magnebot is currently colliding with a wall.

- `objects_static` [Data for all objects in the scene that that doesn't change between frames, such as object IDs, mass, etc.](https://github.com/alters-mit/magnebot/blob/main/doc/api/object_static.md) Key = the ID of the object..


- `magnebot_static` [Data for the Magnebot that doesn't change between frames.](https://github.com/alters-mit/magnebot/blob/main/doc/api/magnebot_static.md)


- `occupancy_map` A numpy array of the occupancy map. This is None until you call `init_scene()`.

Shape = `(1, width, length)` where `width` and `length` are the number of cells in the grid. Each grid cell has a radius of 0.245. To convert from occupancy map `(x, y)` coordinates to worldspace `(x, z)` coordinates, see: `get_occupancy_position()`.

Each element is an integer describing the occupancy at that position.

| Value | Meaning |
| --- | --- |
| -1 | This position is outside of the scene. |
| 0 | Unoccupied and navigable; the Magnebot can go here. |
| 1 | This position is occupied by an object(s) or a wall. |
| 2 | This position is free but not navigable (usually because there are objects in the way. |


The occupancy map is static, meaning that it won't update when objects are moved.

Note that it is possible for the Magnebot to go to positions that aren't "free". The Magnebot's base is a rectangle that is longer on the sides than the front and back. The occupancy grid cell size is defined by the longer axis, so it is possible for the Magnebot to move forward and squeeze into a smaller space. The Magnebot can also push, lift, or otherwise move objects out of its way.

***

## Functions

#### \_\_init\_\_

**`MultiModal()`**

**`MultiModal(port=1071, screen_width=256, screen_height=256)`**

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| port |  int  | 1071 | The socket port. [Read this](https://github.com/threedworld-mit/tdw/blob/master/Documentation/getting_started.md#command-line-arguments) for more information. |
| screen_width |  int  | 256 | The width of the screen in pixels. |
| screen_height |  int  | 256 | The height of the screen in pixels. |

***

### Scene Setup

_These functions should be sent at the start of the simulation._

#### init_scene

**`self.init_scene(scene, layout)`**

**`self.init_scene(scene, layout, trial=None)`**

Initialize a scene and a furniture layout and begin a trial.

```python
from multimodal_challenge import MultiModal

m = MultiModal()
m.init_scene(scene="mm_kitchen_1a", layout=0, trial=57)
```


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| scene |  str |  | The name of the scene. |
| layout |  int |  | The layout index. |
| trial |  int  | None | The trial number. If None, defaults to 0. This loads a snapshot of the scene and the audio data. |

_Returns:_  An `ActionStatus` (always success).

***

### Movement

_These functions move or turn the Magnebot._

_While moving, the Magnebot might start to tip over (usually because it's holding something heavy). If this happens, the Magnebot will stop moving and drop any objects with mass > 30. You can then prevent the Magnebot from tipping over._

#### turn_by

**`self.turn_by(angle)`**

**`self.turn_by(angle, aligned_at=3, stop_on_collision=True)`**

Turn the Magnebot by an angle.

When turning, the left wheels will turn one way and the right wheels in the opposite way, allowing the Magnebot to turn in place.

Possible [return values](https://github.com/alters-mit/magnebot/blob/main/doc/api/action_status.md):

- `success`
- `failed_to_turn`
- `tipping`
- `collision`


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| angle |  float |  | The target angle in degrees. Positive value = clockwise turn. |
| aligned_at |  float  | 3 | If the difference between the current angle and the target angle is less than this value, then the action is successful. |
| stop_on_collision |  bool  | True | If True, if the Magnebot collides with the environment or a heavy object it will stop turning. It will also stop turn if the previous action ended in a collision and was a `turn_by()` in the same direction as this action. Usually this should be True; set it to False if you need the Magnebot to move away from a bad position (for example, to reverse direction if it's starting to tip over). |

_Returns:_  An `ActionStatus` indicating if the Magnebot turned by the angle and if not, why.

#### turn_to

**`self.turn_to(target)`**

**`self.turn_to(target, aligned_at=3, stop_on_collision=True)`**

Turn the Magnebot to face a target object or position.

When turning, the left wheels will turn one way and the right wheels in the opposite way, allowing the Magnebot to turn in place.

Possible [return values](https://github.com/alters-mit/magnebot/blob/main/doc/api/action_status.md):

- `success`
- `failed_to_turn`
- `tipping`
- `collision`


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| target |  Union[int, Dict[str, float] |  | Either the ID of an object or a Vector3 position. |
| aligned_at |  float  | 3 | If the different between the current angle and the target angle is less than this value, then the action is successful. |
| stop_on_collision |  bool  | True | If True, if the Magnebot collides with the environment or a heavy object it will stop turning. Usually this should be True; set it to False if you need the Magnebot to move away from a bad position (for example, to reverse direction if it's starting to tip over). |

_Returns:_  An `ActionStatus` indicating if the Magnebot turned by the angle and if not, why.

#### move_by

**`self.move_by(distance)`**

**`self.move_by(distance, arrived_at=0.3, stop_on_collision=True)`**

Move the Magnebot forward or backward by a given distance.

Possible [return values](https://github.com/alters-mit/magnebot/blob/main/doc/api/action_status.md):

- `success`
- `failed_to_move`
- `collision`
- `tipping`


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| distance |  float |  | The target distance. If less than zero, the Magnebot will move backwards. |
| arrived_at |  float  | 0.3 | If at any point during the action the difference between the target distance and distance traversed is less than this, then the action is successful. |
| stop_on_collision |  bool  | True | If True, if the Magnebot collides with the environment or a heavy object it will stop moving. Usually this should be True; set it to False if you need the Magnebot to move away from a bad position (for example, to reverse direction if it's starting to tip over). |

_Returns:_  An `ActionStatus` indicating if the Magnebot moved by `distance` and if not, why.

#### move_to

**`self.move_to(target)`**

**`self.move_to(target, arrived_at=0.3, aligned_at=3, stop_on_collision=True)`**

Move the Magnebot to a target object or position.

This is a wrapper function for `turn_to()` followed by `move_by()`.

Possible [return values](https://github.com/alters-mit/magnebot/blob/main/doc/api/action_status.md):

- `success`
- `failed_to_move`
- `collision`
- `failed_to_turn`
- `tipping`


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| target |  Union[int, Dict[str, float] |  | Either the ID of an object or a Vector3 position. |
| arrived_at |  float  | 0.3 | While moving, if at any point during the action the difference between the target distance and distance traversed is less than this, then the action is successful. |
| aligned_at |  float  | 3 | While turning, if the different between the current angle and the target angle is less than this value, then the action is successful. |
| stop_on_collision |  bool  | True | If True, if the Magnebot collides with the environment or a heavy object it will stop moving or turning. Usually this should be True; set it to False if you need the Magnebot to move away from a bad position (for example, to reverse direction if it's starting to tip over). |

_Returns:_  An `ActionStatus` indicating if the Magnebot moved to the target and if not, why.

***

### Torso

_These functions adjust the Magnebot's torso._

_While adjusting the torso, the Magnebot is always "immovable", meaning that its wheels are locked and it isn't possible for its root object to move or rotate._

#### set_torso

**`self.set_torso(position)`**

**`self.set_torso(position, angle=None)`**

Slide the Magnebot's torso up or down and optionally rotate it as well.

Possible [return values](action_status.md):

- `success`
- `failed_to_bend` (If the torso failed to reach the target position and/or rotation)


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| position |  float |  | The target vertical position of the torso. Must >=0.6 and <=1.5 |
| angle |  float  | None | If not None, the target rotation of the torso in degrees. The default rotation of the torso is 0. |

_Returns:_  An `ActionStatus` indicating if the torso reached the target position.

***
