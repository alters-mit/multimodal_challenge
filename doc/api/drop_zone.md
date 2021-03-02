# DropZone

`from multimodal_challenge.drop_zone import DropZone`

A DropZone is a circle that is used to define interesting places for an object to drop.
The circle is always on the `(x, z)` plane.

***

## Fields

- `center` The center of the circle as an `[x, y, z]` numpy array.

- `radius` The radius of the circle.

***

## Functions

#### \_\_init\_\_

**`DropZone(center, radius)`**

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| center |  np.array |  | The center of the circle as an `[x, y, z]` numpy array. |
| radius |  float |  | The radius of the circle. |

