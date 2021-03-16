from time import sleep
from tdw.controller import Controller
from tdw.tdw_utils import TDWUtils
from tdw.object_init_data import AudioInitData
from tdw.py_impact import PyImpact, AudioMaterial
from tdw.output_data import Rigidbodies, AudioSources
from magnebot.util import get_data

"""
Test the audio of each target object.
"""

target_objects = ['h-shape_wood_block', 'half_circle_wood_block', 'l-shape_wood_block', 'pentagon_wood_block',
                  'rectangle_wood_block', 'square_wood_block', 'star_wood_block', 't-shape_wood_block', 'fork1',
                  'fork2', 'fork3', 'fork4', 'knife1', 'knife2', 'knife3', 'spoon1', 'spoon2', 'basic_cork_2',
                  'button_two_hole_green_mottled', 'square_coaster_001_cork', 'key_dull_metal',
                  'round_coaster_indent_wood', 'square_coaster_001_marble', 'button_two_hole_red_wood',
                  'round_coaster_cherry', 'button_two_hole_grey', 'square_coaster_rubber',
                  'button_four_hole_red_plastic', 'key_shiny', 'tapered_cork', 'cork_plastic_black',
                  'square_coaster_wood', 'button_four_hole_wood', 'champagne_cork', 'round_coaster_indent_stone',
                  'aaa_battery', 'square_coaster_stone', 'button_four_hole_white_plastic', 'button_four_hole_mottled',
                  'button_four_hole_large_black', 'bung', 'basic_cork', 'round_coaster_indent_rubber',
                  'round_coaster_stone', 'square_coaster_001_wood', '9v_battery', 'button_four_hole_large_wood',
                  'key_brass', 'tapered_cork_w_hole', 'round_coaster_stone_dark', 'button_two_hole_red_mottled',
                  'cork_plastic']
# Get the env audio materials.
floor = AudioMaterial.ceramic
wall = AudioMaterial.wood
floor_resonance_audio = "tile"
wall_resonance_audio = "roughPlaster"
initial_amp = 0.25
# Initialize the scene.
p = PyImpact(initial_amp=initial_amp)
c = Controller(launch_build=False)
c.communicate({"$type": "set_target_framerate",
               "framerate": 100})
for object_name in target_objects:
    print(object_name)
    commands = [c.get_add_scene(scene_name="mm_kitchen_1a"),
                {"$type": "set_floorplan_roof",
                 "show": False}]
    commands.extend(TDWUtils.create_avatar(position={"x": 0, "y": 2, "z": 0}))
    commands.append({"$type": "add_environ_audio_sensor"})
    a = AudioInitData(name=object_name, position={"x": 1, "y": 2.1, "z": -1.7})
    object_id, object_commands = a.get_commands()
    commands.extend(object_commands)
    commands.extend([{"$type": "set_reverb_space_simple",
                      "env_id": -1,
                      "reverb_floor_material": floor_resonance_audio,
                      "reverb_ceiling_material": wall_resonance_audio,
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
