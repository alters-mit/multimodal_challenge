from typing import List
import numpy as np


class MagnebotInitData:
    """
    Initialization data for the Magnebot in the challenge controller and the dataset controller.
    """

    def __init__(self, position: np.array, torso_height: float, column_angle: float,
                 camera_pitch: float, camera_yaw: float):
        """
        :param position: The initial position of the Magnebot as an `[x, y, z]` numpy array.
        :param torso_height: The initial height of the Magnebot's torso (between 0 and 1).
        :param column_angle: The initial rotation of the Magnebot's column in degrees.
        :param camera_pitch: The initial pitch of the Magnebot's camera in degrees.
        :param camera_yaw: The initial yaw of the Magnebot's camera in degrees.
        """

        """:field
        The initial position of the Magnebot as an `[x, y, z]` numpy array.
        """
        self.position: np.array = np.array(position)
        """:field
        The initial height of the Magnebot's torso (between 0 and 1).
        """
        self.torso_height: float = float(torso_height)
        """:field
        The initial rotation of the Magnebot's column in degrees.
        """
        self.column_angle: float = float(column_angle)
        """:field
        The initial pitch of the Magnebot's camera in degrees.
        """
        self.camera_pitch: float = float(camera_pitch)
        """:field
        The initial yaw of the Magnebot's camera in degrees.
        """
        self.camera_yaw: float = float(camera_yaw)
