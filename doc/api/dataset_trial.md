# DatasetTrial

`from multimodal_challenge.dataset_trial import DatasetTrial`

Parameters for defining a trial for dataset generation.

***

## Fields

- `init_data` A [`MultiModalObjectInitData` object](multimodal_object_init_data.md) for the dropped object.

- `force` The initial force of the dropped object object as a Vector3 dictionary.

- `position` The position of the object after it falls. This is used to set a valid initial Magnebot pose.

***

## Functions

#### \_\_init\_\_

**`DatasetTrial(init_data, force, position)`**

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| init_data |  MultiModalObjectInitData |  | A [`MultiModalObjectInitData` object](multimodal_object_init_data.md). |
| force |  Dict[str, float] |  | The initial force of the object as a Vector3 dictionary. |
| position |  Dict[str, float] |  | The position of the object after it falls. This is used to set a valid initial Magnebot pose. |

