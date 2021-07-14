# 0.4.0

- Required version of TDW: 1.8.19.0
- **Added distractor objects.** Objects are randomly placed on the floor during rehearsal.py
  - (Backend) rehearsal.py sets the initial Magnebot position based on where the objects (distractors and target object) have fallen
  - (Backend) `DatasetTrial` now includes initialization data for the distractor objects and the initial Magnebot position
  - (Backend) Added data file `distractor_objects.txt`
- **Removed drop zones** (removed the Python class, all references to drop zones in the documentation, and the cached drop zone positions)
- The target object is now dropped onto a free space of the occupancy map instead of a drop zone
- `dataset.py` now saves occupancy maps as .npy files, which include the position of the target object and the distractor objects
- Added API documentation for Magnebot arm articulation actions (although they have always been usable in this API)
- Improved version checking for the `tdw` pip module, the `magnebot` pip module, and the TDW build
- (Backend): Added `util/add_models.py` to update the model librarian json file
- (Backend): Added `packaging` as a required pip module

# 0.3.6

- Required version of TDW: 1.8.14.0 (Includes size buckets for object audio info)

# 0.3.5

- Required version of TDW: 1.8.13.0

# 0.3.4

- Fixed: `dataset.py` immediately crashes
  - (Backend): Added cached scene bounds data to `multimodal/data/scenes/bounds`

# 0.3.3

- Required version of TDW: 1.8.12.0
- Required version of Magnebot: 1.2.1

# 0.3.2

- Required version of TDW: 1.8.11.1
- Replaced various target objects with new objects that were formerly only in `models_full.json`

# 0.3.1

- Replaced some small target objects with larger target objects
- Set the asset bundles directory/bucket and the dataset directory with environment variables instead of command line arguments
- Added: `download.py` Download asset bundles from the S3 server to a local directory
- (Backend): Added `requests` as a required module

# 0.3.0

- Required version of TDW: 1.8.8
- Required version of Magnebot: 1.2.0
- Added changelog
- Fixed: `MultiModal` doesn't sets the kinematic state incorrectly for some objects
- Removed unused `room` parameter from the constructor of `Dataset`
- Added a table of contents to the API documentation
- (Backend): Refactored and simplified `MultiModalBase`
- (Backend): Removed data files in `multimodal_challenge/data/scenes/bounds` (no longer needed)
- (Backend): Added: `tests/load_scene.py`
