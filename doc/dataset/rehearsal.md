# Rehearsal

`from dataset_generation.rehearsal import Rehearsal`

"Rehearse" the audio dataset_generation by running randomly-generated trials and saving the "valid" trials.

This is meant only for backend developers; the Python module already has cached rehearsal data.

Each scene has a corresponding list of [`DropZones`](../api/drop_zone.md). These are already cached. If the target object lands in a `DropZone`, then this was a valid trial. As a result, this script will cut down on dev time (we don't need to set drop parameters manually) and generation time (because we don't have to discard any audio recordings).

# Requirements

- The `multimodal_challenge` Python module.

# Usage

1. `cd dataset_generation`
2. `python3 rehearsal.py`
3. Run build

# How it works

**Per scene_layout combination** (i.e. scene `mm_kitchen_1_a` layout `0`):

1. Load the corresponding object init data and `DropZone` data.
2. Run trials per scene_layout combination until there's enough (for example, 2000 per scene_layout combination).

**Per trial:**

1. Randomly set the parameters of a new [`Drop`](../api/drop.md) which is used here as initialization data.
2. Let the target object fall. **The only output data is the `Transform` of the target object.**
3. When the target object stops falling, check if the target object is in a `DropZone`. If so, record the `Drop`.

**Result:** A list of `Drop` initialization objects per scene_layout combination:

```
multimodal_challenge/
....data/
........objects/
........scenes/
........dataset/
............drops/
................1_0.json  # scene_layout
................1_1.json
```

### Advantages

- This is a VERY fast process. It saves dev time (we don't need to manually set trial init values) and audio recording time (we don't need to discard any recordings).

### Disadvantages

- All objects in the scene are kinematic because re-initializing the scene per trial would be too slow. Therefore, there will be a small discrepancy between physics behavior in the rehearsal and physics behavior in the dataset.

***

## Fields

- `drop_object` The ID of the dropped object. This changes per trial.

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

_Returns:_  If the object is in the drop zone, a `Drop` object of trial initialization parameters. Otherwise, None.

#### run

**`self.run()`**

**`self.run(num_trials=10000)`**

Generate results for each scene_layout combination.

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| num_trials |  int  | 10000 | The total number of trials. |

#### do_trials

**`self.do_trials(scene, layout, num_trials)`**

Load a scene_layout combination, and its objects, and its drop zones.
Run random trials until we have enough "good" trials, where "good" means that the object landed in a drop zone.
Save the result to disk.

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| scene |  str |  | The scene name. |
| layout |  int |  | The object layout variant of the scene. |
| num_trials |  int |  | How many trials we want to save to disk. |
