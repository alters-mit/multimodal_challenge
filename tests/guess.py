import numpy as np
import vg
from tdw.output_data import ImageSensors, AvatarKinematic
from tdw.tdw_utils import TDWUtils
from magnebot import TestController
from magnebot.util import get_data


class Guess(TestController):
    def guess(self, cone_angle: float = 30) -> None:
        self._start_action()
        # Get the angle between the camera's forward directional vector
        # and the directional vector defined by the camera's position and the guess' position.
        resp = self.communicate([{"$type": "send_image_sensors",
                                 "ids": ["a"]},
                                 {"$type": "send_avatars",
                                  "ids": ["a"]}])
        self._end_action()
        camera_forward = np.array(get_data(resp=resp, d_type=ImageSensors).get_sensor_forward(0))
        camera_position = np.array(get_data(resp=resp, d_type=AvatarKinematic).get_position())

        commands = []
        r = 2
        step = 0.3
        for x in np.arange(-r, r, step=step):
            for y in np.arange(-r, r, step=step):
                for z in np.arange(-r, r, step=step):
                    position = np.array([x, y, z])
                    v = position - camera_position
                    angle = vg.angle(camera_forward, v)
                    assert isinstance(angle, float)
                    # Return success if the position is within the cone and the object is within the sphere.
                    if np.abs(angle) <= cone_angle:
                        commands.append({"$type": "add_position_marker",
                                         "position": TDWUtils.array_to_vector3(position)})
        self.communicate(commands)


if __name__ == "__main__":
    m = Guess()
    m.init_scene()
    m.guess()