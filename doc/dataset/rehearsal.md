# Rehearsal

`from dataset_generation.rehearsal import Rehearsal`

"Rehearse" the audio dataset by running randomly-generated trials and saving the "valid" trials.

This is meant only for backend developers; the Python module already has cached rehearsal data.

Each scene has a corresponding list of [`DropZones`](../api/drop_zone.md). These are already cached.
If the target object lands in a `DropZone`, then this was a valid trial.
As a result, this script will cut down on dev time and generation time.

There will be a small discrepancy in physics behavior when running `dataset.py` because in this controller,
all objects are kinematic (non-moveable) in order to avoid re-initializing the scene per trial (which is slow).

# Requirements

- The `multimodal_challenge` Python module.

# Usage

1. `cd dataset`
2. `python3 rehearsal.py [ARGUMENTS]`
3. Run build

## Environment variables

#### 1. `MULTIMODAL_ASSET_BUNDLES`

**The root directory to download scenes and asset bundles from.** Default value: `"https://tdw-public.s3.amazonaws.com"`

Every scene (room environment) and model (furniture, cabinets, cups, etc.) is stored in TDW as an [asset bundle](https://docs.unity3d.com/Manual/AssetBundlesIntro.html). These asset bundles are downloaded at runtime from a remote S3 server, but it is possible to download them *before* run time and load them locally. **If your Internet connection will make it difficult/slow/impossible to download large US-based files at runtime, we strongly suggest you download them locally.** To do this:

1. `cd path/to/multimodal_challenge`
2. `python3 download.py --dst [DST]`. The `--dst` argument sets the root download directory. Example: `python3 download.py --dst /home/mm_asset_bundles`.

#### 2. `MULTIMODAL_DATASET`

**The directory where the Trial files will be saved.** Default value: `"D:/multimodal_challenge"`

#### How to set the environment variables

Replace `[asset_bundles]` and `[dataset]` with the actual paths. For example: `export MULTIMODAL_ASSET_BUNDLES=/home/mm_asset_bundles`.

| Platform             | Command                                                      |
| -------------------- | ------------------------------------------------------------ |
| OS X or Linux        | `export MULTIMODAL_ASSET_BUNDLES=[asset_bundles] && export MULTIMODAL_DATASET=[dataset] && python3 rehearsal.py` |
| Windows (cmd)        | `set MULTIMODAL_ASSET_BUNDLES=[asset_bundles] && set MULTIMODAL_DATASET=[dataset] && py -3 rehearsal.py` |
| Windows (powershell) | `$env:MULTIMODAL_ASSET_BUNDLES="[asset_bundles]" ; $env:MULTIMODAL_DATASET="[dataset]" ; py -3 rehearsal.py` |

## Arguments

| Argument | Default | Description |
| --- | --- | --- |
| `--random_seed` | 0 | The random seed. |
| `--num_trials` | 10000 | Generate this many trials. |

Example: `python3 rehearsal.py --random_seed 12345 --num_trials 300`

# How it works

**Per scene_layout combination** (i.e. scene `mm_kitchen_1_a` layout `0`):

1. Load the corresponding object init data and `DropZone` data.
2. Run trials per scene_layout combination until there's enough (for example, 2000 per scene_layout combination).

**Per trial:**

1. Randomly set the parameters of a new [`DatasetTrial`](../api/dataset_trial.md) for initialization.
2. Let the target object fall. **The only output data is the `Transform` of the target object.**
3. When the target object stops falling, if it's is in a `DropZone`, record the `DatasetTrial`.

**Result:** A list of `DatasetTrial` initialization objects per scene_layout combination:

```
D:/multimodal_challenge/
....rehearsal/
........mm_kitchen_1a_0.json  # scene_layout
........mm_kitchen_1a_1.json
........(etc.)
```

***

## Fields

- `target_object_id` The ID of the dropped object. This changes per trial.

- `rng` The random number generator.

- `scene_environment` Environment data used for setting drop positions.

- `drop_zones` The drop zones for the current scene.

***

## Functions

#### \_\_init\_\_

**`Rehearsal()`**

**`Rehearsal(port=1071, random_seed=None)`**

Create the network socket and bind the socket to the port.

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| port |  int  | 1071 | The port number. |
| random_seed |  int  | None | The seed used for random numbers. If None, this is chosen randomly. |

#### do_trial

**`self.do_trial()`**

Choose a random object. Assign a random (constrained) scale, position, rotation, and force.
Let the object fall. When it stops moving, determine if the object is in a drop zone.

_Returns:_  Tuple: A `DatasetTrial` if the object landed in the drop zone, otherwise None; drop zone ID.

#### run

**`self.run()`**

**`self.run(num_trials=10000)`**

Generate results for each scene_layout combination.

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| num_trials |  int  | 10000 | The total number of trials. |

#### do_trials

**`self.do_trials(scene, layout, num_trials)`**

**`self.do_trials(scene, layout, num_trials, pbar=None)`**

Load a scene_layout combination, and its objects, and its drop zones.
Run random trials until we have enough "good" trials, where "good" means that the object landed in a drop zone.
Save the result to disk.

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| scene |  str |  | The scene name. |
| layout |  int |  | The object layout variant of the scene. |
| num_trials |  int |  | How many trials we want to save to disk. |
| pbar |  tqdm  | None | Progress bar. |

