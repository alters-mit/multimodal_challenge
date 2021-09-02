# 0.3.10

- Required version of TDW: 1.8.25.0
- Required version of Magnebot: 1.3.1
- Removed some drop zones that often generated trials where the object can't be seen
- Removed some target objects that tend to be too hard to see

# 0.3.9

- Required version of TDW: 1.8.21.0
- Required version of Magnebot: 1.2.2
- Updated furniture layouts to make it easier for the Magnebot to move around 
- (Backend): **Fixed: Crash in `dataset.py` to desktop due to bad Magnebot starting positions.** 
- (Backend): Occupancy maps for objects are much more accurate. These were generated in the `distractors` branch (0.4.0)
- (Backend): There are now separate Magnebot occupancy maps for spawn positions. These were generated in the `distractors` branch (0.4.0)

# 0.3.8

- Required version of TDW: 1.8.19.1

# 0.3.7

- Required version of TDW: 1.8.19.0
- The initial rotation of the Magnebot is totally random (instead of randomly angled away from the target object)

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
