import io

"""
Generate a config.ini file.
"""

asset_bundles = input("Enter the path to the asset bundles. "
                      "If you want to use the models on the remote S3 server, leave this blank (press enter): ")
dataset = input("Enter where you'd like to download or generate the trial dataset files: ")
with io.open("config.ini", "rt", encoding="utf-8") as f:
    f.write(f"asset_bundles={asset_bundles}\ndataset={dataset}")
