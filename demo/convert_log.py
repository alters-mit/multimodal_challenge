from pathlib import Path
from json import loads
import numpy as np

trial = "00126"
agent_data = loads(Path(f"{trial}.json").read_text())["agents"]
path = np.zeros(shape=(len(agent_data), 3))
for i in range(len(agent_data)):
    path[i] = np.array([agent_data[i][0], 0, agent_data[i][2]])
np.save(trial, path)
