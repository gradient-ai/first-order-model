# Model Setup
import io
import os
import subprocess

from base64 import b64decode
from os import environ as env

import imageio
import skimage.io

from skimage.transform import resize
from skimage import img_as_ubyte

from demo import load_checkpoints, make_animation

gen, kp = load_checkpoints("config/vox-256.yaml", env["MODEL"])

_video_reader = imageio.get_reader(env["DRIVING_VIDEO"])

fps = _video_reader.get_meta_data()["fps"]
driving_video = []
try:
    for im in _video_reader:
        driving_video.append(resize(im, (256, 256))[..., :3])
except RuntimeError:
    pass
_video_reader.close()


def generate_adoro(from_image: str, base_path: str):
    _, base64 = from_image.split(",")
    image = skimage.io.imread(b64decode(base64), plugin="imageio")
    source_image = resize(image, (256, 256))[..., :3]
    os.makedirs(base_path, exist_ok=True)
    frames = []
    for index, frame in enumerate(make_animation(source_image, driving_video, gen, kp)):
        frame_bytes = img_as_ubyte(frame)
        imageio.imwrite(f"{base_path}/{index}.jpg", frame_bytes)
        frames.append(frame_bytes)

    generated_video_path = f"{base_path}/generated.mp4"
    imageio.mimsave(generated_video_path, frames, fps=fps)

    video_in = f"""-an -i '{generated_video_path}'"""
    audio_in = f"""-vn -i '{audio_path}'"""
    watermark_in = f"""-an -i '{watermark_path}'"""
    processing = f"""-map 0:v -map 1:a -filter_complex '[0:v][2:v]overlay=156:12'"""
    video_out = f"'{base_path}.mp4'"
    subprocess.run(
        f"""
        ffmpeg {video_in} {audio_in} {watermark_in} {processing} -y -shortest {video_out}
        """,
        check=True, shell=True, timeout=60)

# API Server
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()
app.mount("/public", StaticFiles(directory="public"), name="static_files")
app.mount("/", StaticFiles(directory="web", html=True), name="web")

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/question")
def question():
    return {"answer": 42}


class CreateAdoroRequest(BaseModel):
    image: str


@app.post("/adoro")
def adoro(params: CreateAdoroRequest, background_tasks: BackgroundTasks):
    base_path = f"public/{hash(params.image)}"
    background_tasks.add_task(
        generate_adoro,
        from_image=params.image,
        base_path=base_path,
    )
    return {"path": base_path, "frames": len(driving_video)}
