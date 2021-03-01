# DropZoneAnalyzer

`from dataset_generation.drop_zone_analyzer import DropZoneAnalyzer`

This is a backend tool meant for analyzing the average rate at which objects fall into DropZones.
You can run this after running `rehearsal.py`. You don't need to run this to run `dataset.py`.

***

## Class Variables

| Variable | Type | Description |
| --- | --- | --- |
| `COLOR_A` | np.array | Lerp the position marker colors from this color. |
| `COLOR_B` | np.array | Lerp the position marker colors to this color. |

***

#### run

**`self.run(scene, layout)`**

Every time `rehearsal.py` records `Drop` data, it also records the index of the `DropZone` the object landed in.
This function loads that list of indices, converts them to `add_position_marker` commands, and colorizes them.
Red circles have the most drops and blue circles have the least.

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| scene |  str |  | The name of the scene. |
| layout |  int |  | The layout index. |

