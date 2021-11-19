from typing import Dict
from pathlib import Path
from json import loads, dumps
from tdw.tdw_utils import TDWUtils
from tdw.controller import Controller
from tdw.py_impact import PyImpact
from tdw.output_data import OutputData, AvatarKinematic, Keyboard, ImageSensors, SegmentationColors
from multimodal_challenge.paths import ENV_AUDIO_MATERIALS_PATH, OBJECT_INIT_DIRECTORY
from multimodal_challenge.multimodal_object_init_data import MultiModalObjectInitData
from multimodal_challenge.dataset.env_audio_materials import EnvAudioMaterials


class DatasetDemo(Controller):
    def do_trial(self, scene: str, layout: int, trial: int, show_target_object: bool, initial_amp: float) -> None:
        py_impact = PyImpact(initial_amp=initial_amp)
        # Set the next random seed.
        commands = [{"$type": "set_render_quality",
                     "render_quality": 5},
                    {"$type": "set_target_framerate",
                     "framerate": 60},
                    {"$type": "set_screen_size",
                     "width": 1024,
                     "height": 1024},
                    self.get_add_scene(scene_name=scene),
                    {"$type": "set_aperture",
                     "aperture": 8.0},
                    {"$type": "set_focus_distance",
                     "focus_distance": 2.25},
                    {"$type": "set_post_exposure",
                     "post_exposure": 0.4},
                    {"$type": "set_ambient_occlusion_intensity",
                     "intensity": 0.175},
                    {"$type": "set_ambient_occlusion_thickness_modifier",
                     "thickness": 3.5}]
        # Load object initialization data.
        object_init_data = loads(OBJECT_INIT_DIRECTORY.joinpath(f"{scene}_{layout}.json").read_text(encoding="utf-8"))
        for o in object_init_data:
            o_id, o_commands = MultiModalObjectInitData(**o).get_commands()
            commands.extend(o_commands)
        # Load the trial.
        trial_data = loads(Path(f"rehearsal/{scene}_{layout}.json").read_text(encoding="utf-8"))
        target_object_init_data = MultiModalObjectInitData(**trial_data[trial]["init_data"])
        target_object_init_data.kinematic = False
        target_object_init_data.gravity = True
        target_object_id, target_object_commands = target_object_init_data.get_commands()
        commands.extend(target_object_commands)
        data = loads(ENV_AUDIO_MATERIALS_PATH.read_text(encoding="utf-8"))
        env_audio_materials = EnvAudioMaterials(**data[scene])
        # Apply the force. Enable collision detection.
        commands.extend([{"$type": "apply_force_to_object",
                          "id": target_object_id,
                          "force": trial_data[trial]["force"]},
                         {"$type": "send_collisions",
                          "enter": True,
                          "stay": True,
                          "exit": True,
                          "collision_types": ["obj", "env"]},
                         {"$type": "send_rigidbodies",
                          "frequency": "always"},
                         {"$type": "set_reverb_space_simple",
                          "env_id": -1,
                          "reverb_floor_material": env_audio_materials.floor,
                          "reverb_ceiling_material": "acousticTile",
                          "reverb_front_wall_material": env_audio_materials.wall,
                          "reverb_back_wall_material": env_audio_materials.wall,
                          "reverb_left_wall_material": env_audio_materials.wall,
                          "reverb_right_wall_material": env_audio_materials.wall},
                         {"$type": "send_segmentation_colors"},
                         {"$type": "send_keyboard",
                          "frequency": "always"}])
        # Highlight the target object.
        if show_target_object:
            commands.append({"$type": "add_position_marker",
                             "scale": 0.5,
                             "position": target_object_init_data.position})
        floor = EnvAudioMaterials.RESONANCE_AUDIO_TO_PY_IMPACT[env_audio_materials.floor]
        # Add an avatar.
        avatar_position_directory = Path("avatar_positions")
        if not avatar_position_directory.exists():
            avatar_position_directory.mkdir()
        commands.append({"$type": "create_avatar",
                         "type": "A_Img_Caps_Kinematic",
                         "id": "a"})
        avatar_position_path = avatar_position_directory.joinpath(f"{scene}_{layout}_{trial}.json")
        if avatar_position_path.exists():
            avatar_data = loads(avatar_position_path.read_text())
            commands.extend([{"$type": "teleport_avatar_to",
                              "position": avatar_data["position"]},
                             {"$type": "rotate_avatar_to",
                              "rotation": avatar_data["rotation"]},
                             {"$type": "rotate_sensor_container_to",
                              "rotation": avatar_data["sensor_container_rotation"]}])
        else:
            commands.extend([{"$type": "teleport_avatar_to",
                              "position": {"x": 0, "y": 1.6, "z": 0}}])
        commands.extend([{"$type": "set_anti_aliasing",
                          "mode": "subpixel"},
                         {"$type": "add_environ_audio_sensor"},
                         {"$type": "send_avatars",
                          "frequency": "always"},
                         {"$type": "send_image_sensors",
                          "frequency": "always"}])
        resp = self.communicate(commands)
        done = False
        got_avatar_position = False
        avatar_position: Dict[str, float] = dict()
        avatar_rotation: Dict[str, float] = dict()
        sensor_container_rotation: Dict[str, float] = dict()
        while not done:
            for i in range(len(resp) - 1):
                r_id = OutputData.get_data_type_id(resp[i])
                # Cache default audio info.
                if r_id == "segm":
                    segm = SegmentationColors(resp[i])
                    object_names = dict()
                    for j in range(segm.get_num()):
                        object_names[segm.get_object_id(j)] = segm.get_object_name(j).lower()
                    py_impact.set_default_audio_info(object_names=object_names)
                # Get keyboard input.
                elif r_id == "keyb":
                    keyb = Keyboard(resp[i])
                    for j in range(keyb.get_num_pressed()):
                        k = keyb.get_pressed(j)
                        if k == "Escape":
                            done = True
                            break
                        elif k == "Space":
                            done = True
                            got_avatar_position = True
                            break
                elif r_id == "avki":
                    avki = AvatarKinematic(resp[i])
                    if avki.get_avatar_id() == "a":
                        avatar_position = TDWUtils.array_to_vector3(avki.get_position())
                        avatar_rotation = TDWUtils.array_to_vector4(avki.get_rotation())
                elif r_id == "imse":
                    imse = ImageSensors(resp[i])
                    if imse.get_avatar_id() == "a":
                        sensor_container_rotation = TDWUtils.array_to_vector4(imse.get_sensor_rotation(0))
            if not done:
                resp = self.communicate(py_impact.get_audio_commands(resp=resp, floor=floor, wall=floor,
                                                                     resonance_audio=True))
        # Log the avatar position.
        if got_avatar_position:
            avatar_data = {"position": avatar_position,
                           "rotation": avatar_rotation,
                           "sensor_container_rotation": sensor_container_rotation}
            avatar_position_path.write_text(dumps(avatar_data, indent=2))
        self.communicate({"$type": "terminate"})


if __name__ == "__main__":
    c = DatasetDemo(launch_build=False)

    """
    After the scene is loaded, move and rotate the camera in Unity Editor.
    
    If, while the Unity Editor window is selected (as opposed to the Python console), 
    the controller will receive keyboard input:
    
    1. Spacebar: Save the current avatar position+rotation and quit.
       The next time you load the trial, the avatar will start at this position+rotation.
    2. Esc: Quit without saving the avatar position.
    
    Record with OBS.
    """

    c.do_trial(scene="mm_craftroom_1a",
               layout=0,
               trial=100,
               show_target_object=False,  # If True, add a position marker at the target object's initial position.
               initial_amp=0.9)
