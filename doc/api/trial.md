# Trial

`from multimodal_challenge.trial import Trial`

Data used to initialize a trial. In a trial, the object has already been dropped and generated audio.
This class will place the object at the position at which it stopped moving.
It also includes the pre-recorded audio.

***

## Fields

- `scene` The name of the scene.

- `object_init_data` Initialization data for each object in the scene. Includes the target object.

- `magnebot` [Initialization data for the Magnebot](magnebot_init_data.md).

- `target_object_index` The index of the target object in `object_init_data`.

- `audio` The audio that was recorded while the object was moving.

***

## Functions

#### \_\_init\_\_

**`Trial(scene, magnebot, object_init_data, target_object_index, audio)`**

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| scene |  str |  | The name of the scene. |
| magnebot |  MagnebotInitData |  | [Initialization data for the Magnebot](magnebot_init_data.md). |
| object_init_data |  List[MultiModalObjectInitData] |  | [Initialization data](multimodal_object_init_data.md) for each object in the scene. |
| target_object_index |  int |  | The index of the target object in `object_init_data`. |
| audio |  bytes |  | The audio that was recorded while the object was moving. |

