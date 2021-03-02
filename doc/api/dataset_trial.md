# DatasetTrial

`from multimodal_challenge.dataset_trial import DatasetTrial`

Parameters for defining a trial for dataset generation.

***

## Fields

- `init_data` A [`MultiModalObjectInitData` object](multimodal_object_init_data.md) for the dropped object.

- `force` The initial force of the dropped object object as a Vector3 dictionary.

***

## Functions

#### \_\_init\_\_

**`DatasetTrial(init_data, force)`**

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| init_data |  MultiModalObjectInitData |  | A [`MultiModalObjectInitData` object](multimodal_object_init_data.md). |
| force |  Dict[str, float] |  | The initial force of the object as a Vector3 dictionary. |

