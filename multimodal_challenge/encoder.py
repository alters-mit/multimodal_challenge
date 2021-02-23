from base64 import b64encode
from json import JSONEncoder
import numpy as np
from tdw.py_impact import AudioMaterial, ObjectInfo
from tdw.object_init_data import AudioInitData


class Encoder(JSONEncoder):
    """
    Use this class to encode data to .json for this module.
    """

    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, AudioInitData):
            return obj.__dict__
        elif isinstance(obj, ObjectInfo):
            return obj.__dict__
        elif isinstance(obj, AudioMaterial):
            return obj.name
        elif isinstance(obj, bytes):
            return b64encode(obj).decode("utf-8")
        else:
            print(obj)
            return super(Encoder, self).default(obj)
