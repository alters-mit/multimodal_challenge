from time import sleep
from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from tdw.py_impact import PyImpact, AudioMaterial
from tdw.output_data import Rigidbodies, AudioSources
from magnebot.util import get_data
from multimodal_challenge.util import get_object_init_commands, TARGET_OBJECTS
from multimodal_challenge.multimodal_object_init_data import MultiModalObjectInitData

"""
Test the audio of each target object.
"""


object_init_commands = get_object_init_commands(scene="mm_kitchen_1a", layout=0)

# Get the env audio materials.
floor = AudioMaterial.ceramic
wall = AudioMaterial.wood
floor_resonance_audio = "tile"
wall_resonance_audio = "roughPlaster"
ceiling_resonance_audio = "acousticTile"
initial_amp = 0.25
# Initialize the scene.
p = PyImpact(initial_amp=initial_amp)
c = Controller(launch_build=False)
c.communicate({"$type": "set_target_framerate",
               "framerate": 100})
for object_name in TARGET_OBJECTS:
    print(object_name)
    commands = [c.get_add_scene(scene_name="mm_kitchen_1a"),
                {"$type": "set_floorplan_roof",
                 "show": False}]
    commands.extend(object_init_commands)
    commands.extend(TDWUtils.create_avatar(position={"x": 0, "y": 2, "z": 0}))
    a = MultiModalObjectInitData(name=object_name, position={"x": 1, "y": 2.1, "z": -1.7})
    object_id, object_commands = a.get_commands()
    commands.extend(object_commands)
    commands.extend([{"$type": "set_reverb_space_simple",
                      "env_id": -1,
                      "reverb_floor_material": floor_resonance_audio,
                      "reverb_ceiling_material": ceiling_resonance_audio,
                      "reverb_front_wall_material": wall_resonance_audio,
                      "reverb_back_wall_material": wall_resonance_audio,
                      "reverb_left_wall_material": wall_resonance_audio,
                      "reverb_right_wall_material": wall_resonance_audio},
                     {"$type": "add_environ_audio_sensor"},
                     {"$type": "send_collisions",
                      "collision_types": ["obj", "env"]},
                     {"$type": "send_rigidbodies",
                      "frequency": "always"},
                     {"$type": "send_audio_sources",
                      "frequency": "always"},
                     {"$type": "apply_torque_to_object",
                      "id": object_id,
                      "torque": {"x": 0.2, "y": 0.6, "z": -0.3}},
                     {"$type": "apply_force_to_object",
                      "id": object_id,
                      "force": {"x": -0.07, "y": -0.02, "z": 0.07}}])
    # Start the trial.
    p.set_default_audio_info(object_names={object_id: object_name})
    resp = c.communicate(commands)
    # Loop until the object stops moving and stops making a sound.
    done = False
    while not done:
        rigidbodies = get_data(resp=resp, d_type=Rigidbodies)
        sleeping = False
        for i in range(rigidbodies.get_num()):
            if rigidbodies.get_id(i) == object_id:
                sleeping = rigidbodies.get_sleeping(i)
                break
        audio_sources = get_data(resp=resp, d_type=AudioSources)
        playing = False
        for i in range(audio_sources.get_num()):
            if audio_sources.get_object_id(i) == object_id:
                playing = audio_sources.get_is_playing(i)
                break
        commands = p.get_audio_commands(resp=resp, floor=floor, wall=wall, resonance_audio=True)
        if sleeping and not playing and len(commands) == 0:
            done = True
        else:
            resp = c.communicate(commands)
    p.reset(initial_amp=initial_amp)
    # Wait a bit for the reverb to finish.
    sleep(2)
c.communicate({"$type": "terminate"})
