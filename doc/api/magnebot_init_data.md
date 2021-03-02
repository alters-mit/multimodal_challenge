# MagnebotInitData

`from multimodal_challenge.magnebot_init_data import MagnebotInitData`

Initialization data for the Magnebot in the challenge controller and the dataset controller.

***

## Fields

- `position` The initial position of the Magnebot as an `[x, y, z]` numpy array.

- `rotation` The initial rotation of the Magnebot around the y axis.

- `torso_height` The initial height of the Magnebot's torso (between 0 and 1).

- `column_angle` The initial rotation of the Magnebot's column in degrees.

- `camera_pitch` The initial pitch of the Magnebot's camera in degrees.

- `camera_yaw` The initial yaw of the Magnebot's camera in degrees.

***

## Functions

#### \_\_init\_\_

**`MagnebotInitData(position, rotation, torso_height, column_angle, camera_pitch, camera_yaw)`**

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| position |  np.array |  | The initial position of the Magnebot as an `[x, y, z]` numpy array. |
| rotation |  float |  | The initial rotation of the Magnebot around the y axis. |
| torso_height |  float |  | The initial height of the Magnebot's torso (between 0 and 1). |
| column_angle |  float |  | The initial rotation of the Magnebot's column in degrees. |
| camera_pitch |  float |  | The initial pitch of the Magnebot's camera in degrees. |
| camera_yaw |  float |  | The initial yaw of the Magnebot's camera in degrees. |

