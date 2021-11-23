from typing import List, Tuple, Union
from pathlib import Path
from distutils import file_util
from subprocess import call
from os import chdir
import numpy as np
from PIL import ImageDraw
from tdw.tdw_utils import TDWUtils
from tdw.output_data import OutputData, Images, ScreenPosition, Robot
from magnebot.scene_state import SceneState
from multimodal_challenge.multimodal import MultiModal


class NavigationDemo(MultiModal):
    def __init__(self, port: int = 1071, screen_width: int = 256, screen_height: int = 256):
        self.save_images: bool = False
        super().__init__(port=port, screen_width=screen_width, screen_height=screen_height)
        self.magnebot_screen_positions: List[Tuple[float, float]] = list()
        self.output_directory = Path(f"D:/multimodal_paper_demo")
        if not self.output_directory.exists():
            self.output_directory.mkdir(parents=True)
        self.frame: int = 0
        self.screen_height: int = screen_height

    def do_trial(self, scene: str, layout: int, trial: int) -> None:
        self.magnebot_screen_positions.clear()
        self.output_directory = self.output_directory.joinpath(f"{scene}_{layout}_{trial}")
        if not self.output_directory.exists():
            self.output_directory.mkdir(parents=True)
        self.init_scene(scene=scene, layout=layout, trial=trial)
        self.save_images = True
        self.frame = 0
        # Hide the roof.
        commands = [{"$type": "set_floorplan_roof",
                     "show": False}]
        commands.extend(TDWUtils.create_avatar(avatar_id="c",
                                               position={"x": 0, "y": 11, "z": 0},
                                               look_at={"x": 0, "y": 0, "z": 0}))
        commands.extend([{"$type": "set_pass_masks",
                          "pass_masks": ["_img"],
                          "avatar_id": "c"}])
        resp = self.communicate(commands)
        self.state = SceneState(resp=resp)
        # Get the path to the object.
        navigation_file_path = Path(TDWUtils.zero_padding(trial, 5) + ".npy")
        if not navigation_file_path.exists():
            raise Exception(f"Not found: {navigation_file_path}")
        path = np.load(str(navigation_file_path.resolve()))
        for point in path:
            point = [point[0], 0, point[2]]
            self.move_to(TDWUtils.array_to_vector3(point), stop_on_collision=False)
        self.turn_to(TDWUtils.array_to_vector3([self.state.object_transforms[self.target_object_id].position[0],
                                                0,
                                                self.state.object_transforms[self.target_object_id].position[2]]))
        if self.state.object_transforms[self.target_object_id].position[1] > 0.1:
            self.set_torso(MultiModal._TORSO_MAX_Y)
        self.communicate({"$type": "terminate"})
        # Create the videos.
        for camera in ["egocentric", "top_down"]:
            directory: Path = self.output_directory.joinpath(camera)
            # Change to the directory and call ffmpeg.
            chdir(str(directory.resolve()))
            call(["ffmpeg.exe",
                  "-r", "60",
                  "-i", "%05d.jpg",
                  "-vcodec", "libx264",
                  "-pix_fmt", "yuv420p",
                  f"{camera}.mp4"])
            # Move the file.
            file_util.move_file(src=str(directory.joinpath(f"{camera}.mp4").resolve()),
                                dst=self.output_directory.joinpath(f"{camera}.mp4"))

    def communicate(self, commands: Union[dict, List[dict]]) -> List[bytes]:
        if self.state is not None:
            if isinstance(commands, dict):
                commands = [commands]
            commands.extend([{"$type": "enable_image_sensor",
                              "enable": True,
                              "avatar_id": "a"},
                             {"$type": "send_images"}])
        resp = super().communicate(commands)
        if not self.save_images:
            return resp
        target_object_position = (0, 0)
        for i in range(len(resp) - 1):
            r_id = OutputData.get_data_type_id(resp[i])
            # Get the screen position of the avatar.
            if r_id == "scre":
                scre = ScreenPosition(resp[i])
                screen_position = scre.get_screen()
                screen_position = (screen_position[0], self.screen_height - screen_position[1])
                if scre.get_id() == 0:
                    self.magnebot_screen_positions.append(screen_position)
                else:
                    target_object_position = screen_position
            elif r_id == "robo":
                robo = Robot(resp[i])
                self._next_frame_commands.append({"$type": "send_screen_positions",
                                                  "position_ids": [0, 1],
                                                  "positions": [
                                                      TDWUtils.array_to_vector3(robo.get_position()),
                                                      TDWUtils.array_to_vector3(self.state.object_transforms[
                                                                                    self.target_object_id].position)],
                                                  "ids": ["c"],
                                                  "frequency": "once"})
        # Check if we got images from both cameras.
        avatar_images = dict()
        for i in range(len(resp) - 1):
            r_id = OutputData.get_data_type_id(resp[i])
            # Get images.
            if r_id == "imag":
                images = Images(resp[i])
                for j in range(images.get_num_passes()):
                    if images.get_pass_mask(j) == "_img":
                        avatar_images[images.get_avatar_id()] = {"images": images, "_img": j}
                        break
        # We got images from both cameras. Save them.
        if len(avatar_images) == 2:
            # Save the egocentric image.
            egocentric_directory = self.output_directory.joinpath("egocentric")
            if not egocentric_directory.exists():
                egocentric_directory.mkdir(parents=True)
            egocentric_directory.joinpath(f"{TDWUtils.zero_padding(self.frame, 5)}.jpg").\
                write_bytes(avatar_images["a"]["images"].get_image(index=avatar_images["a"]["_img"]))
            # Save the top-down image.
            top_down_directory = self.output_directory.joinpath("top_down")
            if not top_down_directory.exists():
                top_down_directory.mkdir(parents=True)
            # Get a PIL image.
            pil_image = TDWUtils.get_pil_image(images=avatar_images["c"]["images"], index=avatar_images["c"]["_img"])
            # Draw the path.
            draw = ImageDraw.Draw(pil_image)
            for k in range(len(self.magnebot_screen_positions) - 1):
                # Draw a line.
                draw.line([(self.magnebot_screen_positions[k][0], self.magnebot_screen_positions[k][1]),
                           (self.magnebot_screen_positions[k + 1][0], self.magnebot_screen_positions[k + 1][1])],
                          width=4,
                          joint="curve",
                          fill=(0, 174, 239, 255))
            # Draw a box.
            r = 18
            draw.rectangle([(target_object_position[0] - r, target_object_position[1] - r),
                            (target_object_position[0] + r, target_object_position[1] + r)],
                           outline=(255, 0, 0, 255),
                           fill=None,
                           width=4)
            # Save the image.
            pil_image.save(str(top_down_directory.joinpath(f"{TDWUtils.zero_padding(self.frame, 5)}.jpg").resolve()))
            # Increment the frame counter.
            self.frame += 1
        return resp


if __name__ == "__main__":
    NavigationDemo(screen_width=1024, screen_height=1024).do_trial(scene="mm_craftroom_2b", layout=0, trial=126)
