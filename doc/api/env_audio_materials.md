# EnvAudioMaterials

`from multimodal_challenge.env_audio_materials import EnvAudioMaterials`

PyImpact and Resonance Audio materials for the floor and walls of a scene.

***

## Class Variables

| Variable | Type | Description |
| --- | --- | --- |
| `PY_IMPACT_TO_RESONANCE_AUDIO` | Dict[AudioMaterial, str] | A dictionary. Key = A PyImpact `AudioMaterial`. Value = The corresponding Resonance Audio material. |

***

## Fields

- `floor` The PyImpact floor floor material.

- `wall` The PyImpact wall audio material.

***

## Functions

#### \_\_init\_\_

**`EnvAudioMaterials(floor, wall)`**

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| floor |  str |  | The PyImpact floor audio material as a string. |
| wall |  str |  | The PyImpact wall audio material as a string. |

