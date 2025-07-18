from fastapi import FastAPI, UploadFile, File, WebSocket, WebSocketDisconnect, Form
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
import zipfile
import io
import json
from .render import render_report
from . import tasks
import asyncio
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://datatodoc.de/q2report-editor",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    await websocket.accept()

    async def send_func(msg):
        await websocket.send_text(msg)

    tasks.register_websocket(task_id, send_func)
    try:
        await websocket.receive_text()  # optional: wait for any msg
        while task_id in tasks.task_progress:
            await websocket.send_text(tasks.task_progress[task_id])
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        pass
    finally:
        tasks.unregister_websocket(task_id)


@app.post("/upload/")
async def upload(file: UploadFile = File(...), format: str = Form(...)):
    task_id = tasks.create_task_id()

    contents = await file.read()
    try:
        with zipfile.ZipFile(io.BytesIO(contents)) as z:
            report_json = z.read("report.json").decode()
            data_json = json.loads(z.read("data.json"))
    except Exception as e:
        return {"error": "Invalid zip", "details": str(e)}

    async def job():
        result = await render_report(
            report_json, data_json, format, lambda msg: tasks.update_progress(task_id, msg)
        )
        tasks.save_result(task_id, result)
        await tasks.update_progress(task_id, "done")

    import asyncio

    asyncio.create_task(job())

    return {"task_id": task_id}


@app.get("/status/{task_id}")
async def status(task_id: str):
    result = tasks.get_status(task_id)
    if not result:
        return {"error": "Not ready or invalid task_id"}
    print("status", datetime.now())
    return {"status": "done"}


@app.get("/download/{task_id}")
async def download(task_id: str):
    result = tasks.get_result(task_id)
    if not result:
        return {"error": "Not ready or invalid task_id"}
    return Response(
        content=result,
        media_type="application/octet-stream",
        headers={"Content-Disposition": "attachment; filename=report.zip"},
    )
