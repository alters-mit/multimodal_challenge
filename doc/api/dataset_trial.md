# DatasetTrial

`from multimodal_challenge.dataset_trial import DatasetTrial`

Parameters for defining a trial for dataset generation.

***

## Fields

- `target_object` target_object: [`MultiModalObjectInitData` initialization data](multimodal_object_init_data.md) for the target object.

- `force` The initial force of the target object as a Vector3 dictionary.

- `magnebot_position` The initial position of the Magnebot.

- `target_object_position` The final position of the target object.

- `distractors` Initialization data for the distractor objects.

***

## Functions

#### \_\_init\_\_

**`DatasetTrial(target_object, force, magnebot_position, target_object_position, distractors)`**

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| target_object |  MultiModalObjectInitData |  | [`MultiModalObjectInitData` initialization data](multimodal_object_init_data.md) for the target object. |
| force |  Dict[str, float] |  | The initial force of the target object as a Vector3 dictionary. |
| magnebot_position |  Dict[str, float] |  | The initial position of the Magnebot. |
| target_object_position |  Dict[str, float] |  | The final position of the target object. |
| distractors |  List[Union[dict, MultiModalObjectInitData] |  | Initialization data for the distractor objects. |

