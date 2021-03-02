import numpy as np


class DropZone:
    """
    A DropZone is a circle that is used to define interesting places for an object to drop.
    The circle is always on the `(x, z)` plane.
    """

    def __init__(self, center: np.array, radius: float):
        """
        :param center: The center of the circle as an `[x, y, z]` numpy array.
        :param radius: The radius of the circle.
        """

        """:field
        The center of the circle as an `[x, y, z]` numpy array. The circle is always on the `(x, z)` plane.
        """
        self.center: np.array = center
        """:field
        The radius of the circle.
        """
        self.radius: float = radius
