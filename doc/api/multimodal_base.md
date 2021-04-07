# MultiModalBase

`from multimodal_challenge.multimodal_base import MultiModalBase`

Abstract class controller for the MultiModal challenge.
The code in this controller shared between [`Dataset`](../dataset/dataset.md) and [`MultiModal`](multimodal.md).

***

## Fields

- `target_object_id` The ID of the target object.

***

## Functions

#### \_\_init\_\_

**`MultiModalBase()`**

**`MultiModalBase(port=1071, screen_width=256, screen_height=256, random_seed=None, skip_frames=10)`**

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| port |  int  | 1071 | The socket port. [Read this](https://github.com/threedworld-mit/tdw/blob/master/Documentation/getting_started.md#command-line-arguments) for more information. |
| screen_width |  int  | 256 | The width of the screen in pixels. |
| screen_height |  int  | 256 | The height of the screen in pixels. |
| random_seed |  int  | None | The seed used for random numbers. If None, this is chosen randomly. In the Magnebot API this is used only when randomly selecting a start position for the Magnebot (see the `room` parameter of `init_scene()`). The same random seed is used in higher-level APIs such as the Transport Challenge. |
| skip_frames |  int  | 10 | The build will return output data this many physics frames per simulation frame (`communicate()` call). This will greatly speed up the simulation, but eventually there will be a noticeable loss in physics accuracy. If you want to render every frame, set this to 0. |

#### init_scene

**`self.init_scene(scene, layout)`**

**Always call this function before starting a new trial.**

Initialize a scene and a furniture layout. Add and position the Magnebot and dropped object.


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| scene |  str |  | The name of the scene. |
| layout |  int |  | The layout index. |

_Returns:_  An `ActionStatus` (always success).

