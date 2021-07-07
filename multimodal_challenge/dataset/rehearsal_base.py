from abc import ABC, abstractmethod
from pathlib import Path
from json import dumps
from typing import Optional, List, TypeVar, Generic
from tqdm import tqdm
from overrides import final
import numpy as np
from tdw.controller import Controller
from magnebot.scene_environment import SceneEnvironment
from multimodal_challenge.util import get_object_init_commands, get_scene_librarian, get_scene_layouts
from multimodal_challenge.encoder import Encoder
from multimodal_challenge.dataset.dataset_trial_base import DatasetTrialBase

T = TypeVar("T", bound=DatasetTrialBase)


class RehearsalBase(Controller, ABC, Generic[T]):
    """
    Abstract base class for defining pre-cached data that will be used by dataset.py
    """

    def __init__(self, port: int = 1071, random_seed: int = None):
        """
        :param port: The socket port for connecting to the build.
        :param random_seed: The random seed. If None, a seed will be generated.
        """

        super().__init__(port=port, launch_build=False, check_version=True)
        self.output_directory: Path = self._get_output_directory()
        if not self.output_directory.exists():
            self.output_directory.mkdir(parents=True)
        # Get a random seed.
        if random_seed is None:
            random_seed = self.get_unique_id()
        # Write the random seed.
        self.output_directory.joinpath("seed.txt").write_text(str(random_seed), encoding="utf-8")
        """:field
        The random number generator.
        """
        self.rng: np.random.RandomState = np.random.RandomState(random_seed)
        """:field
        Environment data used for setting drop positions.
        """
        self.scene_environment: Optional[SceneEnvironment] = None

    @final
    def run(self, num_trials: int = 10000) -> None:
        """
        Generate results for each scene_layout combination.

        :param num_trials: The total number of trials.
        """

        self.scene_librarian = get_scene_librarian()
        # Get the total number of scene_layout combinations.
        scene_layouts = get_scene_layouts()
        num_layouts = 0.0
        for k in scene_layouts:
            num_layouts += scene_layouts[k]
        # Do trials for each scene_layout combination.
        trials_per_scene_layout = int(np.ceil(num_trials / num_layouts))
        pbar = tqdm(total=int(trials_per_scene_layout * num_layouts))
        for scene in scene_layouts:
            for layout in range(scene_layouts[scene]):
                self._do_trials(scene=scene, layout=layout, num_trials=trials_per_scene_layout, pbar=pbar)
        pbar.close()
        self.communicate({"$type": "terminate"})

    def _do_trials(self, scene: str, layout: int, num_trials: int, pbar: tqdm) -> None:
        """
        Load a scene_layout combination, and its objects, and its drop zones.
        Run random trials until we have enough "good" trials, where "good" means that the object landed in a drop zone.
        Save the result to disk.

        :param scene: The scene name.
        :param layout: The object layout variant of the scene.
        :param num_trials: How many trials we want to save to disk.
        :param pbar: Progress bar.
        """

        self._set_potential_object_positions(scene=scene, layout=layout)
        scene_record = self.scene_librarian.get_record(scene)
        commands: List[dict] = [{"$type": "add_scene",
                                 "name": scene_record.name,
                                 "url": scene_record.get_url()},
                                {"$type": "send_environments"},
                                {"$type": "enable_reflection_probes",
                                 "enable": False},
                                {"$type": "destroy_all_objects"}]
        commands.extend(get_object_init_commands(scene=scene, layout=layout))
        # Make all objects kinematic.
        for i in range(len(commands)):
            if commands[i]["$type"] == "set_kinematic_state":
                commands[i]["is_kinematic"] = True
        resp = self.communicate(commands)
        # Set the scene environment.
        self.scene_environment = SceneEnvironment(resp=resp)
        close_bar = pbar is None
        if pbar is None:
            pbar = tqdm(total=num_trials)
        pbar.set_description(f"{scene}_{layout}")
        # Remember all good trials.
        dataset_trials: List[T] = list()
        while len(dataset_trials) < num_trials:
            # Do a trial.
            dataset_trial = self._do_trial()
            if dataset_trial is not None:
                # Save the data.
                dataset_trials.append(dataset_trial)
                pbar.update(1)
        # Write the results to disk.
        self.output_directory.joinpath(f"{scene}_{layout}.json").write_text(dumps(dataset_trials, cls=Encoder),
                                                                            encoding="utf-8")
        if close_bar:
            pbar.close()

    @abstractmethod
    def _get_output_directory(self) -> Path:
        """
        :return: The name of the root output directory.
        """

        raise Exception()

    @abstractmethod
    def _set_potential_object_positions(self, scene: str, layout: int) -> None:
        """
        Set potential initial positions for any objects not defined by the floorplan layouts.

        :param scene: The current scene.
        :param layout: The current layout.
        """

        raise Exception()

    @abstractmethod
    def _do_trial(self) -> Optional[T]:
        """
        Do a single trial.

        :return: An object defining the result of the trial. If None, the trial was bad and will be skipped.
        """

        raise Exception()
