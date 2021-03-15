import numpy as np


class MagnebotInitData:
    """
    Initialization data for the Magnebot in the challenge controller and the dataset controller.
    """

    def __init__(self, position: np.array, rotation: np.array):
        """
        :param position: The initial position of the Magnebot as an `[x, y, z]` numpy array.
        :param rotation: The initial rotation of the Magnebot as an `[x, y, z, w]` numpy array.
        """

        """:field
        The initial position of the Magnebot as an `[x, y, z]` numpy array.
        """
        self.position: np.array = np.array(position)
        """:field
        The initial rotation of the Magnebot as an `[x, y, z, w]` numpy array.
        """
        self.rotation: np.array = rotation
