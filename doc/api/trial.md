# Trial

`from multimodal_challenge.trial import Trial`

Data used to initialize a trial. In a trial, the object has already been dropped and generated audio.
This class will place the Magnebot and every object in the scene at the position at which it stopped moving.

***

## Fields

- `object_init_data` Initialization data for each object in the scene. Includes the target object.

- `target_object_index` The index of the target object in `object_init_data`.

- `magnebot_position` The position of the Magnebot as an `[x, y, z]` numpy array.

- `magnebot_rotation` The rotation of the Magnebot as an `[x, y, z, w]` numpy array.

***

## Functions

#### \_\_init\_\_

**`Trial(magnebot_position, magnebot_rotation, object_init_data, target_object_index)`**

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| magnebot_position |  np.array |  | The position of the Magnebot as an `[x, y, z]` numpy array. |
| magnebot_rotation |  np.array |  | The rotation of the Magnebot as an `[x, y, z, w]` numpy array. |
| object_init_data |  List[MultiModalObjectInitData] |  | [Initialization data](multimodal_object_init_data.md) for each object in the scene. |
| target_object_index |  int |  | The index of the target object in `object_init_data`. |

