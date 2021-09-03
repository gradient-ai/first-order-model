# Model Setup
from os import env

import imageio

from skimage.transform import resize
from skimage import img_as_ubyte

from demo import load_checkpoints, make_animation

gen, kp = load_checkpoints("config/vox-adv-256.yaml", env["CHECKPOINT_PATH"])

_video_reader = imageio.get_reader(env["DRIVING_VIDEO_PATH"])

fps = _video_reader.get_meta_data()["fps"]
driving_video = [resize(frame, (256, 256))[..., :3] for frame in _video_reader]

# API Server
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles


app = FastAPI()
app.mount("/public", StaticFiles(directory="public"), name="static_files")


@app.get("/question")
def question():
    return {"answer": 42}


@app.post("/adoro")
def adoro(reference_png_base64: str):
    source_image = imageio.imread(reference_png_base64)
    source_image = resize(source_image, (256, 256))[..., :3]
    frames = [
        img_as_ubyte(frame)
        for frame in make_animation(source_image, driving_video, gen, kp)
    ]
    output_path = "public/result.mp4"
    imageio.mimsave(output_path, frames, fps=fps)
    return {"path": output_path}
