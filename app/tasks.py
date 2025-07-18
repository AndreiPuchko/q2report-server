import uuid
from typing import Dict, Callable

task_results: Dict[str, bytes] = {}
task_progress: Dict[str, str] = {}
websockets: Dict[str, Callable[[str], None]] = {}


def create_task_id() -> str:
    return str(uuid.uuid4())


def register_websocket(task_id: str, send_func: Callable[[str], None]):
    websockets[task_id] = send_func


def unregister_websocket(task_id: str):
    websockets.pop(task_id, None)


async def update_progress(task_id: str, message: str):
    print(task_id, message)
    task_progress[task_id] = message
    if task_id in websockets:
        await websockets[task_id](message)


def save_result(task_id: str, result: bytes):
    task_results[task_id] = result


def get_result(task_id: str):
    return task_results.pop(task_id, None)


def get_status(task_id: str):
    return task_id in task_results
