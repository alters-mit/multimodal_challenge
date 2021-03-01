# MultiModalObjectInitData

`from multimodal_challenge.multimodal_object_init_data import MultiModalObjectInitData`

Object initialization data for the Multi-Modal Challenge.
This is exactly the same as `AudioInitData` except that it will always set the library to the local library.

***

#### \_\_init\_\_

**`MultiModalObjectInitData(name)`**

**`MultiModalObjectInitData(name, scale_factor=None, position=None, rotation=None, kinematic=False)`**

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| name |  str |  | The name of the model. |
| scale_factor |  Dict[str, float] | None | The scale factor. |
| position |  Dict[str, float] | None | The initial position. If None, defaults to: `{"x": 0, "y": 0, "z": 0`}. |
| rotation |  Dict[str, float] | None | The initial rotation as Euler angles or a quaternion. If None, defaults to: `{"w": 1, "x": 0, "y": 0, "z": 0}` |
| kinematic |  bool  | False | If True, the object will be kinematic. |

