# TDW Multi-Modal Challenge

Search for a dropped object in a room using the [Magnebot API](https://github.com/alters-mit/magnebot) and pre-calculated audio that was generated by a physics simulation of the falling object.


# Setup

1. `git clone https://github.com/alters-mit/multimodal_challenge.git`
2. `cd path/to/multimodal_challenge` (replace `path/to` with the actual path)
3. `pip3 install -e .`

# `MultiModal` challenge controller

Use a `MultiModal` controller to initialize a scene, populate it with objects (including the target object), and load the corresponding audio data.

**[Read the API documentation.](doc/api/multimodal.md)**

```python
from multimodal_challenge.multimodal import MultiModal

m = MultiModal()
m.init_scene(scene="mm_kitchen_1a", layout=0, trial=57)
```

# Audio Dataset Generation

![](doc/images/dataset.png)

## `init_data.py`

This is a backend tool for TDW  developers to convert saved [TDW commands](https://github.com/threedworld-mit/tdw/blob/master/Documentation/api/command_api.md) into [initialization instructions](doc/api/multimodal_object_init_data.md). It will also create [metadata records](https://github.com/threedworld-mit/tdw/blob/master/Documentation/python/librarian/librarian.md), [`DropZone`](doc/api/drop_zone.md) data, and occupancy maps.

[Further documentation here.](doc/dataset/init_data.md)

## `rehearsal.py`

Define [`DatasetTrial`](doc/api/dataset_trial.md) initialization parameters for target objects. Drop the object. If it lands in a [`DropZone`](doc/api/drop_zone.md), record the `DatasetTrial`. This will give `dataset.py` initialization parameters.

[Further documentation here.](doc/dataset/rehearsal.md)

## `dataset.py`

Use the initialization data generated by `rehearsal.py` to create [`Trials`](doc/api/trial.md). A `Trial` is initialization data for each object in the scene (position, rotation, etc.), initialization data for the Magenbot, and a .wav file.

[Further documentation here.](doc/dataset/rehearsal.md)