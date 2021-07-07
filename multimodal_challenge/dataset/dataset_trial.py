from typing import Dict, List
from multimodal_challenge.multimodal_object_init_data import MultiModalObjectInitData


class DatasetTrial:
    """
    Parameters for defining a trial for dataset generation.
    """

    def __init__(self, target_object: MultiModalObjectInitData, force: Dict[str, float],
                 target_object_position: Dict[str, float],
                 distractors: List[MultiModalObjectInitData]):
        """
        :param target_object: [`MultiModalObjectInitData` initialization data](multimodal_object_init_data.md) for the target object.
        :param force: The initial force of the target object as a Vector3 dictionary.
        :param target_object_position: The position of the object after it falls. This is used to set a valid initial Magnebot pose.
        :param distractors: Initialization data for the distractor objects.
        """

        # Load the drop parameters from a dictionary.
        if isinstance(target_object, dict):
            target_object: dict
            """:field
            target_object: [`MultiModalObjectInitData` initialization data](multimodal_object_init_data.md) for the target object.
            """
            self.target_object = MultiModalObjectInitData(**target_object)
        else:
            self.target_object: MultiModalObjectInitData = target_object
        """:field
        The initial force of the target object as a Vector3 dictionary.
        """
        self.force: Dict[str, float] = force
        """:field
        The position of the target object after it falls. This is used to set a valid initial Magnebot pose.
        """
        self.target_object_position: Dict[str, float] = target_object_position
        """:field
        Initialization data for the distractor objects.
        """
        self.distractors: List[MultiModalObjectInitData] = distractors
