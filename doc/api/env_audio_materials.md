# EnvAudioMaterials

`from multimodal_challenge.env_audio_materials import EnvAudioMaterials`

PyImpact and Resonance Audio materials for the floor and walls of a scene.

***

## Class Variables

| Variable | Type | Description |
| --- | --- | --- |
| `RESONANCE_AUDIO_TO_PY_IMPACT` | Dict[str, AudioMaterial] | A dictionary. Key = A Resonance Audio material. Value = The corresponding PyImpact `AudioMaterial`. |

***

## Fields

- `floor` The Resonance Audio floor material.

- `wall` The Resonance Audio wall material.

***

## Functions

#### \_\_init\_\_

**`EnvAudioMaterials(floor, wall)`**

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| floor |  str |  | The Resonance Audio floor material. |
| wall |  str |  | The Resonance Audio wall material. |

