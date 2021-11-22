from typing import Dict
from pathlib import Path
from json import loads, dumps
from tdw.tdw_utils import TDWUtils
from tdw.controller import Controller
from tdw.add_ons.py_impact import PyImpact
from tdw.add_ons.resonance_audio_initializer import ResonanceAudioInitializer
from tdw.output_data import OutputData, AvatarKinematic, Keyboard, ImageSensors
from multimodal_challenge.paths import ENV_AUDIO_MATERIALS_PATH, OBJECT_INIT_DIRECTORY
from multimodal_challenge.dataset.env_audio_materials import EnvAudioMaterials


class DatasetDemo(Controller):
    def do_trial(self, scene: str, layout: int, trial: int, show_target_object: bool, initial_amp: float) -> None:
        data = loads(ENV_AUDIO_MATERIALS_PATH.read_text(encoding="utf-8"))
        env_audio_materials = EnvAudioMaterials(**data[scene])
        py_impact = PyImpact(initial_amp=initial_amp,
                             floor=ResonanceAudioInitializer.AUDIO_MATERIALS[env_audio_materials.floor])
        audio = ResonanceAudioInitializer(floor=env_audio_materials.floor,
                                          right_wall=env_audio_materials.wall,
                                          left_wall=env_audio_materials.wall,
                                          front_wall=env_audio_materials.wall,
                                          back_wall=env_audio_materials.wall)
        self.add_ons.extend([py_impact, audio])
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
                     "thickness": 3.5},
                    {"$type": "send_keyboard",
                     "frequency": "always"}]
        # Load object initialization data.
        object_init_data = loads(OBJECT_INIT_DIRECTORY.joinpath(f"{scene}_{layout}.json").read_text(encoding="utf-8"))
        for o in object_init_data:
            commands.extend(self.get_add_physics_object(model_name=o["name"],
                                                        position=o["position"],
                                                        rotation=o["rotation"],
                                                        kinematic=True,
                                                        scale_factor=o["scale_factor"],
                                                        object_id=self.get_unique_id()))
        # Add the target object.
        trial_data = loads(Path(f"rehearsal/{scene}_{layout}.json").read_text(encoding="utf-8"))
        target_object_id = self.get_unique_id()
        target_object_data = trial_data[trial]["init_data"]
        commands.extend(self.get_add_physics_object(model_name=target_object_data["name"],
                                                    position=target_object_data["position"],
                                                    rotation=target_object_data["rotation"],
                                                    kinematic=False,
                                                    scale_factor=target_object_data["scale_factor"],
                                                    object_id=target_object_id))
        # Apply the force.
        commands.append({"$type": "apply_force_to_object",
                         "id": target_object_id,
                         "force": trial_data[trial]["force"]})
        # Highlight the target object.
        if show_target_object:
            commands.append({"$type": "add_position_marker",
                             "scale": 0.5,
                             "position": target_object_data["position"]})
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
                # Get keyboard input.
                if r_id == "keyb":
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
                resp = self.communicate([])
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
