from pathlib import Path
from py_md_doc import PyMdDoc
import re

if __name__ == "__main__":
    # API documentation.
    md = PyMdDoc(input_directory=Path("../multimodal_challenge"), files=["dataset/dataset_trial.py",
                                                                         "dataset/drop_zone.py",
                                                                         "dataset/env_audio_materials.py",
                                                                         "multimodal_object_init_data.py",
                                                                         "magnebot_init_data.py",
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
    # Append fields.
    magnebot_fields = re.search(r"## Fields\n((.|\n)*?)\*", magnebot_api, flags=re.MULTILINE).group(1)
    doc = re.sub(r"## Fields\n((.|\n)*?)\*", r"## Fields\1" + magnebot_fields + "*", doc)
    # Append other sections.
    sections = ""
    toc = ""
    for s in ["Frames", "Parameter types", "Class Variables"]:
        section = re.search(f"## {s}\n" + r"((.|\n)*?)\*\*\*", magnebot_api, flags=re.MULTILINE).group(0)
        sections += section + "\n\n"
        toc += f"- [{s}](#{s})\n"
    doc = re.sub(r"## Fields", sections + "\n## Fields\n", doc)
    # Create a table of contents.
    function_txt = doc.split("## Functions")[1]
    functions = "- [Functions](#Functions)\n"
    for line in function_txt.split("\n"):
        # API section.
        if line.startswith("#### "):
            header = line.split("#### ")[1]
            if header == r"\_\_init\_\_":
                functions += f"  - [{header}](#{header})\n"
            else:
                functions += f"  - [{header}](#{header})\n"
    toc += functions
    doc = doc.replace("[TOC]", toc)
    Path("../doc/api/multimodal.md").write_text(doc, encoding="utf-8")

    # Dataset generation documentation.
    md = PyMdDoc(input_directory=Path("../dataset_generation"), files=["dataset.py", "rehearsal.py", "init_data.py",
                                                                       "drop_zone_analyzer.py"])
    md.get_docs(output_directory=Path("../doc/dataset"))
