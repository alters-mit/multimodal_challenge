from multimodal_challenge.multimodal_object_init_data import TransformInitData

"""
Copy models_core.json to the multimodal library.
"""

lib_mm = list(TransformInitData.LIBRARIES.values())[-1]
lib_core = TransformInitData.LIBRARIES["models_core.json"]

for record_core in lib_core.records:
    record_mm = lib_mm.get_record(record_core.name)
    if record_mm is not None:
        continue
    record_core.urls = {k: v.replace("https://tdw-public.s3.amazonaws.com", "ROOT")
                        for (k, v) in record_core.urls.items()}
    lib_mm.add_or_update_record(record=record_core, overwrite=False, write=False)
lib_mm.write()
