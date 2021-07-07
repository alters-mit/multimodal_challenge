from typing import Dict
from multimodal_challenge.multimodal_object_init_data import MultiModalObjectInitData
from multimodal_challenge.dataset.dataset_trial_base import DatasetTrialBase


class DatasetTrial(DatasetTrialBase):
    """
    Parameters for defining a trial for dataset generation.
    """

    def __init__(self, init_data: MultiModalObjectInitData, force: Dict[str, float], position: Dict[str, float]):
        """
        :param init_data: A [`MultiModalObjectInitData` object](multimodal_object_init_data.md).
        :param force: The initial force of the object as a Vector3 dictionary.
        :param position: The position of the object after it falls. This is used to set a valid initial Magnebot pose.
        """

        # Load the drop parameters from a dictionary.
        if isinstance(init_data, dict):
            init_data: dict
            """:field
            A [`MultiModalObjectInitData` object](multimodal_object_init_data.md) for the dropped object.
            """
            self.init_data = MultiModalObjectInitData(**init_data)
        else:
            self.init_data: MultiModalObjectInitData = init_data
        """:field
        The initial force of the dropped object object as a Vector3 dictionary.
        """
        self.force: Dict[str, float] = force
        """:field
        The position of the object after it falls. This is used to set a valid initial Magnebot pose.
        """
        self.position: Dict[str, float] = position
