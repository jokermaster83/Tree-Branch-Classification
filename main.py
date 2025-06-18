from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
from io import BytesIO
import os
import uuid
import asyncio
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager

from src.branch_classification import branch_classification
from src.fruit_forecast import fruit_forecast
from src.prunning_branches import prunning_branches
from src.skeleton_extraction import skeleton_extraction
from src.skeleton_label_fixed import skeleton_label_fixed
from src.skeleton_parent_fixed import skeleton_parent_fixed
from src.keypoints_swc import keypoints_swc
from src.upload_file_url import upload_file_url

TASKS = {}
BASE_DIR = "./data"
os.makedirs(BASE_DIR, exist_ok=True)

FILE_LIFETIME_SECONDS = 1800  
CLEANUP_INTERVAL = 300        
executor = ThreadPoolExecutor(max_workers=64)

STAGE_PROGRESS = {
    "initializing": 0,
    "downloading": "5%",
    "skeleton_extraction": "20%",
    "skeleton_processing": "40%",
    "parallel_tasks": "60%",
    "done": "100%",
    "error": -1
}

def is_old_file(file_path):
    allowed_extensions = {".obj", ".swc", ".ply", ".json"}
    if not os.path.isfile(file_path):
        return False
    _, ext = os.path.splitext(file_path)
    if ext.lower() not in allowed_extensions:
        return False
    return (time.time() - os.path.getmtime(file_path)) > FILE_LIFETIME_SECONDS

def cleanup_old_files():
    for filename in os.listdir(BASE_DIR):
        file_path = os.path.join(BASE_DIR, filename)
        try:
            if is_old_file(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"[Cleanup Error] {file_path}: {e}")

def periodic_cleanup():
    def loop():
        while True:
            time.sleep(CLEANUP_INTERVAL)
            cleanup_old_files()
    thread = threading.Thread(target=loop, daemon=True)
    thread.start()

@asynccontextmanager
async def lifespan(app: FastAPI):
    periodic_cleanup()
    yield

app = FastAPI(lifespan=lifespan)

class ModelInput(BaseModel):
    obj_url: str

def download_obj_file(url: str) -> BytesIO:
    response = requests.get(url)
    response.raise_for_status()
    return BytesIO(response.content)

async def async_download_obj_file(url: str) -> BytesIO:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, download_obj_file, url)

async def async_skeleton_extraction(obj_path, swc_path):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, skeleton_extraction, obj_path, swc_path)

async def async_skeleton_processing(swc_path):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, skeleton_parent_fixed, swc_path)
    await loop.run_in_executor(executor, skeleton_label_fixed, swc_path)

async def async_keypoints_only(swc_path, swc_keypoints_path, task_id):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, keypoints_swc, swc_path, swc_keypoints_path)
    TASKS[task_id]["result"]["swc_file_url"] = upload_file_url(swc_keypoints_path)

async def async_branch_classification(swc_path, output_path, task_id):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, branch_classification, swc_path, output_path)
    TASKS[task_id]["result"]["branch_classification_file_url"] = upload_file_url(output_path)

async def async_fruit_forecast(swc_path, output_path, task_id):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, fruit_forecast, swc_path, output_path)
    TASKS[task_id]["result"]["json_file_url"] = upload_file_url(output_path)

async def async_prunning_branches(swc_path, output_path, task_id):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, prunning_branches, swc_path, output_path)
    TASKS[task_id]["result"]["prunning_branches_file_url"] = upload_file_url(output_path)

async def process_model_task(task_id: str, input_data: ModelInput):
    try:
        TASKS[task_id]["status"] = "running"
        TASKS[task_id]["stage"] = "downloading"
        TASKS[task_id]["progress"] = STAGE_PROGRESS["downloading"]

        obj_path = os.path.join(BASE_DIR, f"{task_id}_input.obj")
        swc_path = os.path.join(BASE_DIR, f"{task_id}_output.swc")
        swc_keypoints_path = os.path.join(BASE_DIR, f"{task_id}_output_keypoints.swc")
        json_path = os.path.join(BASE_DIR, f"{task_id}_output.json")
        branch_classification_path = os.path.join(BASE_DIR, f"{task_id}_branch_classification.ply")
        prunning_branches_path = os.path.join(BASE_DIR, f"{task_id}_prunning_branches.ply")

        obj_file = await async_download_obj_file(input_data.obj_url)
        with open(obj_path, "wb") as f:
            f.write(obj_file.read())

        TASKS[task_id]["stage"] = "skeleton_extraction"
        TASKS[task_id]["progress"] = STAGE_PROGRESS["skeleton_extraction"]
        await async_skeleton_extraction(obj_path, swc_path)

        TASKS[task_id]["stage"] = "skeleton_processing"
        TASKS[task_id]["progress"] = STAGE_PROGRESS["skeleton_processing"]
        await async_skeleton_processing(swc_path)

        TASKS[task_id]["stage"] = "parallel_tasks"
        TASKS[task_id]["progress"] = STAGE_PROGRESS["parallel_tasks"]
        await asyncio.gather(
            async_keypoints_only(swc_path, swc_keypoints_path, task_id),
            async_branch_classification(swc_path, branch_classification_path, task_id),
            async_fruit_forecast(swc_path, json_path, task_id),
            async_prunning_branches(swc_path, prunning_branches_path, task_id)
        )

        TASKS[task_id]["status"] = "success"
        TASKS[task_id]["stage"] = "done"
        TASKS[task_id]["progress"] = STAGE_PROGRESS["done"]

    except Exception as e:
        TASKS[task_id]["status"] = "failed"
        TASKS[task_id]["stage"] = "error"
        TASKS[task_id]["progress"] = STAGE_PROGRESS["error"]
        TASKS[task_id]["error"] = str(e)

@app.post("/process_model/")
async def run_processing_task(input_data: ModelInput):
    task_id = str(uuid.uuid4())
    TASKS[task_id] = {
        "status": "pending",
        "stage": "initializing",
        "progress": STAGE_PROGRESS["initializing"],
        "result": {
            "swc_file_url": "",
            "branch_classification_file_url": "",
            "json_file_url": "",
            "prunning_branches_file_url": ""
        },
        "error": ""
    }
    print(f"[Task {task_id}] Created and started processing...")
    asyncio.create_task(process_model_task(task_id, input_data))
    return {"task_id": task_id}

@app.get("/task_status/{task_id}")
async def get_task_status(task_id: str):
    task = TASKS.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task ID not found")
    return task

