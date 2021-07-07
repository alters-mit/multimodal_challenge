# DatasetTrial

`from multimodal_challenge.dataset_trial import DatasetTrial`

Parameters for defining a trial for dataset generation.

***

## Fields

- `target_object` target_object: [`MultiModalObjectInitData` initialization data](multimodal_object_init_data.md) for the target object.

- `force` The initial force of the target object as a Vector3 dictionary.

- `target_object_position` The position of the target object after it falls. This is used to set a valid initial Magnebot pose.

- `distractors` Initialization data for the distractor objects.

***

## Functions

#### \_\_init\_\_

**`DatasetTrial(target_object, force, target_object_position, distractors)`**

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| target_object |  MultiModalObjectInitData |  | [`MultiModalObjectInitData` initialization data](multimodal_object_init_data.md) for the target object. |
| force |  Dict[str, float] |  | The initial force of the target object as a Vector3 dictionary. |
| target_object_position |  Dict[str, float] |  | The position of the object after it falls. This is used to set a valid initial Magnebot pose. |
| distractors |  List[MultiModalObjectInitData] |  | Initialization data for the distractor objects. |

