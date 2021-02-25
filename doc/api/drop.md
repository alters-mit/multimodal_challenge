# Drop

`from multimodal_challenge.drop import Drop`

Parameters for defining a dropped object: its starting position, rotation, etc. plus a force vector.

***

## Fields

- `init_data` An [`MultiModalObjectInitData` object](multimodal_object_init_data.md).

- `force` The initial force of the object as a Vector3 dictionary.

***

## Functions

#### \_\_init\_\_

**`Drop(init_data, force)`**

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| init_data |  MultiModalObjectInitData |  | A [`MultiModalObjectInitData` object](multimodal_object_init_data.md). |
| force |  Dict[str, float] |  | The initial force of the object as a Vector3 dictionary. |

