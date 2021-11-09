# TDW Multi-Modal Challenge

Search for a dropped object in a room using the [Magnebot API](https://github.com/alters-mit/magnebot) and pre-calculated audio that was generated by a physics simulation of the falling object.

# Setup

1. If you currently have `tdw` installed: `pip3 uninstall tdw`
2. If you currently have `magnebot` installed: `pip3 uninstall magnebot`
3. `git clone https://github.com/alters-mit/multimodal_challenge.git`
4. `cd multimodal_challenge`
5. `git checkout distractors`
6. `pip3 install -e .`
7. Download [TDW build 1.8.29](https://github.com/threedworld-mit/tdw/releases/tag/v1.8.29)
8. (Optional) Download the asset bundles (read [this](doc/api/multimodal.md) for more information).

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

This is a backend tool for TDW  developers to convert saved [TDW commands](https://github.com/threedworld-mit/tdw/blob/master/Documentation/api/command_api.md) into [initialization instructions](doc/api/multimodal_object_init_data.md).

[Further documentation here.](doc/dataset/init_data.md)

## `occupancy_mapper.py`

This script generates and saves two occupancy maps:

1. An occupancy map indicating which cells are free, occupied by an object, or not within the scene
2. An occupancy map indicating where a Magnebot can be added to the scene.

[Further documentation here.](doc/dataset/occupancy_mapper.md)

## `rehearsal.py`

Define [`DatasetTrial`](doc/api/dataset_trial.md) initialization parameters for distractor objects and the target object. Drop the objects. If they land in acceptable positions, and if there is a position to add the Magnebot in the scene, record the `DatasetTrial`. This will give `dataset.py` initialization parameters.

[Further documentation here.](doc/dataset/rehearsal.md)

## `dataset.py`

Use the initialization data generated by `rehearsal.py` to create [`Trials`](doc/api/trial.md). A `Trial` is initialization data for each object in the scene (position, rotation, etc.), initialization data for the Magenbot, a .wav file of the audio, and an occupancy map as a .npy file.

[Further documentation here.](doc/dataset/dataset.md)

# Changelog

[Changelog](doc/changelog.md)