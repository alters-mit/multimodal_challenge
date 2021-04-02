from pathlib import Path
from py_md_doc import PyMdDoc
import re

if __name__ == "__main__":
    # API documentation.
    md = PyMdDoc(input_directory=Path("../multimodal_challenge"), files=["dataset/dataset_trial.py",
                                                                         "dataset/drop_zone.py",
                                                                         "dataset/env_audio_materials.py",
                                                                         "multimodal_object_init_data.py",
                                                                         "multimodal_base.py",
                                                                         "occupancy_mapper.py",
                                                                         "trial.py"])
    md.get_docs(output_directory=Path("../doc/api"))

    # Multimodal API documentation.
    md = PyMdDoc(input_directory=Path("../multimodal_challenge"), files=["multimodal.py"],
                 metadata_path=Path("doc_metadata.json"))
    doc = md.get_doc(Path("../multimodal_challenge/multimodal.py"))
    # Get the Magnebot API. This assumes that it's located in the home directory.
    magnebot_api = Path.home().joinpath("magnebot/doc/api/magnebot_controller.md").read_text(encoding="utf-8")
    # Fix relative links.
    magnebot_api = re.sub(r"\[(.*)\]\((?!https)(.*)\.md\)",
                          r"[\1](https://github.com/alters-mit/magnebot/blob/main/doc/api/\2.md)", magnebot_api)
    # Remove code examples.
    magnebot_api = re.sub(r"(```python((.|\n)*?)```\n)", "", magnebot_api)
    # Remove this paragraph.
    magnebot_api = re.sub(r"(Images of occupancy maps can be found(.*)\.\n\n)", "", magnebot_api, flags=re.MULTILINE)
    # Get all of the movement actions from the Magnebot API.
    api_txt = re.search(r"(### Movement((.|\n)*?))#", magnebot_api, flags=re.MULTILINE).group(1)
    actions = []
    for action in ["turn_by", "turn_to", "move_by", "move_to"]:
        api_txt += re.search(f"(#### {action}((.|\n)*?))#", magnebot_api, flags=re.MULTILINE).group(1)
    # Append the movement actions before the Torso section.
    doc = re.sub(r"((.|\n)*?)(### Torso)", r"\1" + api_txt + "***\n\n" + r"\3", doc)
    # Append camera actions.
    doc += "### Camera\n\n_These commands rotate the Magnebot's camera or add additional camera to the scene." \
           " They advance the simulation by exactly 1 frame._\n\n"
    for action in ["rotate_camera", "reset_camera"]:
        doc += re.search(f"(#### {action}((.|\n)*?))#", magnebot_api, flags=re.MULTILINE).group(1)

    # Append misc.
    doc += "### Misc.\n\n_These are utility functions that won't advance the simulation by any frames._\n\n"
    for action in ["get_occupancy_position", "get_visible_objects", "end"]:
        doc += re.search(f"(#### {action}((.|\n)*?))#", magnebot_api, flags=re.MULTILINE).group(1)

    # Append class variables.
    magnebot_class_vars = re.search(f"## Class Variables" + r"\n((.|\n)*?)\*$", magnebot_api,
                                    flags=re.MULTILINE).group(1). \
        replace("| Variable | Type | Description |\n| --- | --- | --- |", "").strip()
    doc = re.sub(f"## Class Variables" + r"\n((.|\n)*?)\n\*", "## Class Variables\n" + r"\1" + magnebot_class_vars, doc)
    # Append fields.
    magnebot_fields = re.search(f"## Fields" + r"\n((.|\n)*?)\*$", magnebot_api, flags=re.MULTILINE).group(1)
    doc = re.sub(f"## Fields" + r"\n((.|\n)*?)\n\*", "## Fields" + r"\1" + magnebot_fields, doc)

    # Append other sections.
    sections = ""
    for s in ["Frames", "Parameter types"]:
        section = re.search(f"## {s}\n" + r"((.|\n)*?)\*\*\*", magnebot_api, flags=re.MULTILINE).group(0)
        sections += section + "\n\n"
    doc = re.sub(r"## Fields", sections + "\n## Fields\n", doc)
    doc = doc.replace("[TOC-MM]", PyMdDoc.get_toc(doc)).replace("****", "***").replace("\n\n\n", "\n\n")
    Path("../doc/api/multimodal.md").write_text(doc, encoding="utf-8")

    # Dataset generation documentation.
    md = PyMdDoc(input_directory=Path("../dataset_generation"), files=["dataset.py", "rehearsal.py", "init_data.py"])
    md.get_docs(output_directory=Path("../doc/dataset"))
