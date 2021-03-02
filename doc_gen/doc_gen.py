from pathlib import Path
from py_md_doc import PyMdDoc

if __name__ == "__main__":
    # API documentation.
    md = PyMdDoc(input_directory=Path("../multimodal_challenge"), files=["dataset/dataset_trial.py",
                                                                         "dataset/drop_zone.py",
                                                                         "dataset/env_audio_materials.py",
                                                                         "multimodal_object_init_data.py",
                                                                         "magnebot_init_data.py",
                                                                         "trial.py"],
                 metadata_path=Path("doc_metadata.json"))
    md.get_docs(output_directory=Path("../doc/api"))
    # Dataset generation documentation.
    md = PyMdDoc(input_directory=Path("../dataset_generation"), files=["dataset.py", "rehearsal.py", "init_data.py",
                                                                       "drop_zone_analyzer.py", "occupancy_mapper.py"])
    md.get_docs(output_directory=Path("../doc/dataset"))
