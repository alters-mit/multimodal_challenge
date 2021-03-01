from typing import Dict
from multimodal_challenge.multimodal_object_init_data import MultiModalObjectInitData


class Drop:
    """
    Parameters for defining a dropped object: its starting position, rotation, etc. plus a force vector.
    """

    def __init__(self, init_data: MultiModalObjectInitData, force: Dict[str, float]):
        """
        :param init_data: A [`MultiModalObjectInitData` object](multimodal_object_init_data.md).
        :param force: The initial force of the object as a Vector3 dictionary.
        """

        # Load the drop parameters from a dictionary.
        if isinstance(init_data, dict):
            init_data: dict
            """:field
            A [`MultiModalObjectInitData` object](multimodal_object_init_data.md).
            """
            self.init_data = MultiModalObjectInitData(**init_data)
        else:
            self.init_data: MultiModalObjectInitData = init_data
        """:field
        The initial force of the object as a Vector3 dictionary.
        """
        self.force: Dict[str, float] = force
