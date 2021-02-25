from pathlib import Path
from py_md_doc import PyMdDoc


if __name__ == "__main__":
    # API documentation.
    md = PyMdDoc(input_directory=Path("../multimodal_challenge"), files=["dataset_generation/drop.py",
                                                                         "dataset_generation/drop_zone.py",
                                                                         "multimodal_object_init_data.py",
                                                                         "trial.py"],
                 metadata_path=Path("doc_metadata.json"))
    md.get_docs(output_directory=Path("../doc/api"))
    md = PyMdDoc(input_directory=Path("../dataset_generation"), files=["dataset.py", "rehearsal.py"])
    md.get_docs(output_directory=Path("../doc/dataset"))
