# Trial

`from multimodal_challenge.trial import Trial`

Data used to initialize a trial. In a trial, the object has already been dropped and generated audio.
This class will place the object at the position at which it stopped moving.
It also includes the pre-recorded audio.

***

## Fields

- `scene` The name of the scene.

- `object_init_data` Initialization data for each object in the scene. Includes the target object.

- `magnebot_position` The initial position of the Magnebot.

- `magnebot_rotation` The initial rotation of the Magnebot in degrees.

- `torso_height` The initial height of the Magnebot's torso.

- `column_rotation` The initial rotation of the Magnebot's column.

- `camera_pitch` The pitch of the camera in degrees.

- `camera_yaw` The yaw of the camera in degrees.

- `target_object` The object ID of the target object.

- `audio` The audio that was recorded while the object was moving.

***

## Functions

#### \_\_init\_\_

**`Trial(scene, magnebot_position, magnebot_rotation, torso_height, column_rotation, camera_pitch, camera_yaw, object_init_data, target_object, audio)`**

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| scene |  str |  | The name of the scene. |
| magnebot_position |  np.array |  | The initial position of the Magnebot as an `[x, y, z]` numpy array. |
| magnebot_rotation |  float |  | The initial rotation of the Magnebot in degrees. |
| torso_height |  float |  | The initial height of the Magnebot's torso. |
| column_rotation |  float |  | The initial rotation of the Magnebot's column. |
| camera_pitch |  float |  | The pitch of the camera in degrees. |
| camera_yaw |  float |  | The yaw of the camera in degrees. |
| object_init_data |  List[MultiModalObjectInitData] |  | [Initialization data](multimodal_object_init_data.md) for each object in the scene. Includes the target object. |
| target_object |  int |  | The object ID of the target object. |
| audio |  bytes |  | The audio that was recorded while the object was moving. |

#### write

**`self.write(path)`**

Serialize this object into JSON and write to disk.

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| path |  Path |  | The filepath. |

