from typing import Dict, List
from multimodal_challenge.dataset.dataset_trial_base import DatasetTrialBase


class DistractorTrial(DatasetTrialBase):
    """
    Parameters for defining a trial for dataset generation.
    """

    def __init__(self, names: List[str], positions: List[Dict[str, float]], rotations: List[Dict[str, float]]):
        """
        :param names: The name of each object.
        :param positions: The position of each object.
        :param rotations: The rotation of each object as a quaternion.
        """

        """:field
        The name of each object.
        """
        self.name: List[str] = names
        """:field
        The position of each object.
        """
        self.positions: List[Dict[str, float]] = positions
        """:field
        The rotation of each object as a quaternion.
        """
        self.rotations: List[Dict[str, float]] = rotations
