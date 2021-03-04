from typing import List
import numpy as np
from tdw.tdw_utils import TDWUtils


class MagnebotInitData:
    """
    Initialization data for the Magnebot in the challenge controller and the dataset controller.
    """

    def __init__(self, position: np.array, rotation: float):
        """
        :param position: The initial position of the Magnebot as an `[x, y, z]` numpy array.
        :param rotation: The initial rotation of the Magnebot around the y axis in degrees.
        """

        """:field
        The initial position of the Magnebot as an `[x, y, z]` numpy array.
        """
        self.position: np.array = np.array(position)
        """:field
        The initial rotation of the Magnebot around the y axis in degrees.
        """
        self.rotation: float = float(rotation)

    def get_commands(self) -> List[dict]:
        """
        :return: A list of commands to initialize a Magnebot pose.
        """

        return [{"$type": "teleport_robot_euler_angles",
                 "position": TDWUtils.array_to_vector3(self.position),
                 "rotation": {"x": 0, "y": self.rotation, "z": 0}},
                {"$type": "set_immovable",
                 "immovable": True}]
