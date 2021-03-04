from typing import Dict, List
from tdw.py_impact import PyImpact, AudioMaterial, ObjectInfo
from tdw.output_data import Rigidbodies, AudioSources
from magnebot import TestController, ActionStatus
from magnebot.util import get_data


class Audio(TestController):
    def __init__(self, port: int = 1071):
        super().__init__(port=port, skip_frames=0)
        self.p = PyImpact(initial_amp=0.5)

    def init_scene(self, scene: str = None, layout: int = None, room: int = None) -> ActionStatus:
        super().init_scene()
        object_names = dict()
        for o_id in self.objects_static:
            object_names[o_id] = self.objects_static[o_id].name
        for j in self.magnebot_static.joints:
            object_names[j] = self.magnebot_static.joints[j].name
        self.p.set_default_audio_info(object_names=object_names)
        # Assign audio properties per joint.
        for j in self.magnebot_static.joints:
            self.p.object_info[self.magnebot_static.joints[j].name] = ObjectInfo(
                name=self.magnebot_static.joints[j].name,
                mass=self.magnebot_static.joints[j].mass,
                amp=0.05,
                resonance=0.65,
                material=AudioMaterial.metal,
                bounciness=0.6,
                library="")

    def run(self) -> None:
        self._start_action()
        self._next_frame_commands.extend([{"$type": "send_rigidbodies",
                                           "frequency": "always"},
                                          {"$type": "send_audio_sources",
                                           "frequency": "always"}])
        resp = self.communicate([])
        done = False
        while not done:
            rigidbodies = get_data(resp=resp, d_type=Rigidbodies)
            audio = get_data(resp=resp, d_type=AudioSources)
            playing = False
            for i in range(audio.get_num()):
                if audio.get_is_playing(i):
                    playing = True
                    break
            commands = self.p.get_audio_commands(resp=resp, floor=AudioMaterial.ceramic, wall=AudioMaterial.wood)
            for cmd in commands:
                if cmd["$type"] == "play_audio_data":
                    if cmd["id"] in self.magnebot_static.joints:
                        name = self.magnebot_static.joints[cmd["id"]].name
                    elif cmd["id"] in self.objects_static:
                        name = self.objects_static[cmd["id"]].name
                    else:
                        name = "env"
                    print(cmd["id"], name)
            done = rigidbodies.get_sleeping(0) and not playing and len(commands) == 0
            resp = self.communicate(commands)

    def _get_scene_init_commands(self, magnebot_position: Dict[str, float] = None) -> List[dict]:
        self._add_object(model_name="fork2", position={"x": 0.05, "y": 3, "z": 0})
        commands = super()._get_scene_init_commands(magnebot_position=magnebot_position)
        commands.append({"$type": "add_audio_sensor"})
        return commands


if __name__ == "__main__":
    m = Audio()
    m.init_scene()
    m.run()
    m.end()
