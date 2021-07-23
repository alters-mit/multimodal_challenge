from argparse import ArgumentParser
from pathlib import Path
from platform import system
from tqdm import tqdm
from requests import get
from tdw.librarian import ModelLibrarian, SceneLibrarian
from multimodal_challenge.paths import OBJECT_LIBRARY_PATH, SCENE_LIBRARY_PATH

"""
Download every scene and model asset bundle used in this challenge from the remote S3 server to a local directory.
"""


def download() -> None:
    """
    Download the asset bundle.
    """

    pbar.set_description(f"{record.name}")
    p = record.urls[system()].split("ROOT")[1][1:]
    dst = dst_dir.joinpath(p)
    if dst.exists():
        pbar.update(1)
        return
    if record.do_not_use:
        pbar.update(1)
        return
    if not dst.parent.exists():
        dst.parent.mkdir(parents=True)
    # Download the asset bundle.
    if record.name in double_slashes:
        url = bucket + "/" + str(Path(p).parent).replace("\\", "/") + "//" + record.name
    else:
        url = bucket + "/" + p
    resp = get(url)
    assert resp.status_code == 200, (url, resp.status_code)
    # Save the scene.
    dst.write_bytes(resp.content)
    pbar.update(1)


if __name__ == "__main__":
    bucket = "https://tdw-public.s3.amazonaws.com"
    double_slashes = ['baking_sheet01', 'baking_sheet02', 'jigsaw_puzzle_composite', 'puzzle_box_composite',
                      'rattan_basket', 'stack_of_cups_composite']
    parser = ArgumentParser()
    parser.add_argument("--dst", type=str, default="D:/multimodal_asset_bundles", help="The root download directory.")
    args = parser.parse_args()

    # Create the root output directory.
    dst_dir = Path(args.dst)
    if not dst_dir.exists():
        dst_dir.mkdir(parents=True)

    # Download all scenes.
    scene_lib = SceneLibrarian(library=str(SCENE_LIBRARY_PATH.resolve()))
    pbar = tqdm(total=len(scene_lib.records))
    for record in scene_lib.records:
        download()
    pbar.close()

    # Download all models.
    # Download all scenes.
    model_lib = ModelLibrarian(library=str(OBJECT_LIBRARY_PATH.resolve()))
    pbar = tqdm(total=len(model_lib.records))
    for record in model_lib.records:
        download()
    pbar.close()
