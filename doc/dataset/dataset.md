# Dataset

`from dataset_generation.dataset import Dataset`

Use the initialization data generated by [`rehearsal.py`](rehearsal.md) to create [`Trials`](../api/trial.md). A `Trial` is initialization data for each object in the scene (position, rotation, etc.), initialization data for the Magenbot, and a .wav file.

# Requirements

- The `multimodal_challenge` Python module
- Initialization data. Do one of the following:
  1. To use pre-calculated initialization data, download the rehearsal data (LINK TBD) and extract it to the root directory (see below):
  ```
  D:/multimodal_challenge
  ....rehearsal.zip
  ....rehearsal/
  ........mm_craftroom_1a_0.json
  ........(etc.)
  ```
  2. To create new initialization data, run [`rehearsal.py`](rehearsal.md) to generate the initialization data.

- Audio drivers
- [fmedia](https://stsaz.github.io/fmedia/)
- ffmpeg
- [`PyAudio`](https://people.csail.mit.edu/hubert/pyaudio/) If you're using Windows and Python 3.7 or later, use a wheel from [this site](https://www.lfd.uci.edu/~gohlke/pythonlibs/) and install it via: `pip3 install path/to/the/downloaded.whl` (replace this with the actual path to the downloaded file)

# Usage

1. `cd dataset`
2. `[ENV VARIABLES] python3 dataset.py [ARGUMENTS]`
3. Run build

This will take approximately 8 hours to complete. It can be stopped and restarted without losing progress.

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
| OS X or Linux        | `export MULTIMODAL_ASSET_BUNDLES=[asset_bundles] && export MULTIMODAL_DATASET=[dataset] && python3 dataset.py` |
| Windows (cmd)        | `set MULTIMODAL_ASSET_BUNDLES=[asset_bundles] && set MULTIMODAL_DATASET=[dataset] && py -3 dataset.py` |
| Windows (powershell) | `$env:MULTIMODAL_ASSET_BUNDLES="[asset_bundles]" ; $env:MULTIMODAL_DATASET="[dataset]" ; py -3 dataset.py` |

## Arguments

| Argument | Default | Description |
| --- | --- | --- |
| `--random_seed` | 0 | The random seed. |

Example: `python3 dataset.py --random_seed 12345`

# How it works

**Per scene_layout combination:**

1. Load the corresponding object init data and the [`DatasetTrial`](../api/dataset_trial.md) data from rehearsal.py

**Per trial:**

1. Re-initialize the scene.
2. Select the next `DatasetTrial` initialization object in the list.
3. Add a Magnebot. Turn the Magnebot away from `DatasetTrial.position`. Set random position and rotation parameters.
4. Add the target object from the `DatasetTrial` parameters (position, force, etc.)
5. Initialize audio in the scene and audio recording.
6. Let the object fall. Use PyImpact to generate collisions.
7. The trial stops either when the sound stops playing or if a maximum number of frames has been reached.
8. Save the results to disk.

**Result:** A directory dataset files. The dataset has a `random_seeds.npy` file that is used to select random seeds per trial.

Each trial is saved in a `scene_layout` directory and has three files:

1. A .json file of the [`Trial` data](../api/trial.md).
2. An audio .wav audio file.
3. The occupancy map as a .npy numpy file.

```
D:/multimodal_challenge/
....random_seeds.npy
....mm_kitchen_1a_0/  # scene_layout
........00000.json
........00000.wav
........00000.npy
........00001.json
........00001.wav
........00001.npy
........(etc.)
....mm_kitchen_1a_1/
```

***

## Class Variables

| Variable | Type | Description |
| --- | --- | --- |
| `PY_AUDIO` | pyaudio.PyAudio | The PyAudio object. This is used to determine when a trial ends (when the audio stops playing). |
| `INITIAL_AMP` | float | PyImpact initial amp value. |
| `PY_IMPACT` | PyImpact | The PyImpact object used to generate impact sound audio at runtime. |
| `TEMP_AUDIO_PATH` | Path | The path to the temporary audio file. |

***

## Fields

- `trial_count` The name of the next trial.

- `scene` The name of the scene in the current trial.

- `layout` The name of the layout of the current trial.

- `trials` Parameters to define each trial. See: `rehearsal.py`.

- `target_object_id` The ID of the target object in the current trial.

- `env_audio_materials` The PyImpact audio materials used for the environment as an `EnvAudioMaterials` object.

- `env_id` A dummy object ID for the environment. This is reassigned per trial.

***

## Functions

#### \_\_init\_\_

**`Dataset()`**

**`Dataset(port=1071, random_seed=0, log=True)`**

Create the network socket and bind the socket to the port.

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| port |  int  | 1071 | The port number. |
| random_seed |  int  | 0 | The seed for the random number generator. |
| log |  bool  | True | If True, log each list of commands sent. |

#### run

**`self.run()`**

Generate the entire dataset for each scene_layout combination.

#### do_trials

**`self.do_trials(scene, layout, pbar)`**

Get the cached trial initialization data for a scene_layout combination and do each trial.
This will try to avoid overwriting existing trial results.
This will start a thread to listen to audio on the sound card to determine if a trial is done.

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| scene |  str |  | The name of the scene. |
| layout |  int |  | The index of the furniture layout. |
| pbar |  tqdm |  | The progress bar. |

#### do_trial

**`self.do_trial(output_directory)`**

Initialize the scene. This will add the target (dropped) object, the scene objects, and the Magnebot,
as well as set a position, rotation, torso height, column rotation, and camera angles for the Magnebot.

Start recording audio and let the object fall. The simulation ends when there's no more audio or
if the simulation continued for too long.

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| output_directory |  Path |  | The output directory for the trial data. |

#### init_scene

**`self.init_scene(scene, layout)`**

Initialize the scene. Turn the Magnebot away from the object. Let the object fall.


| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| scene |  str |  | The name of the scene. |
| layout |  int |  | The layout index. |

_Returns:_  An `ActionStatus` (always success).

#### communicate

**`self.communicate()`**

Source: https://stackoverflow.com/questions/892199/detect-record-audio-in-python

Loop until audio stops playing.

