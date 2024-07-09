from fastapi import FastAPI, APIRouter, Path, HTTPException
from pydantic import BaseModel
import threading
import time
import os
from random import randint
from typing import List, Dict, Any

app = FastAPI()

# Defining the lock
threadLock = threading.Lock()

# First project
class ResponseModel(BaseModel):
    message: str

def my_func1(thread_number):
    return f"My function called by thread N° {thread_number}"

@app.get("/run-thread/{thread_number}", response_model=ResponseModel)
def run_thread(thread_number: int = Path(...)):
    if thread_number != 6:
        raise HTTPException(status_code=400, detail="thread_number must be 6")

    result = {"message": ""}

    def target_func():
        nonlocal result
        result["message"] = my_func1(thread_number)

    t = threading.Thread(target=target_func)
    t.start()
    t.join()

    return result

# Second project
class Result(BaseModel):
    thread_number: int
    result: int
    message: str

def my_func2(thread_number: int):
    result = thread_number * 2
    if thread_number % 2 == 0:
        message = f'thread N°{thread_number}: over number'
    else:
        message = f'thread N°{thread_number}: string number'
    return Result(thread_number=thread_number, result=result, message=message)

@app.get("/execute/{thread_number}", response_model=Result)
async def execute(thread_number: int = Path(..., ge=0, le=100)):
    result = await run_in_thread2(thread_number)
    return result

async def run_in_thread2(thread_number: int):
    loop = threading.Event()
    result_container = {}

    def target():
        nonlocal result_container
        result_container['result'] = my_func2(thread_number)
        loop.set()

    threading.Thread(target=target).start()
    loop.wait()
    return result_container['result']

# Third project
class MyThreadClass(threading.Thread):
    def __init__(self, name, duration):
        threading.Thread.__init__(self)
        self.name = name
        self.duration = duration
        self.result = None

    def run(self):
        # Acquire lock
        threadLock.acquire()
        try:
            pid = os.getpid()
            start_time = time.time()
            print(f"---> {self.name} running, belonging to process ID {pid}\n")
            time.sleep(self.duration)
            self.result = {
                "name": self.name,
                "pid": pid,
                "duration": self.duration,
                "start_time": start_time,
                "end_time": time.time()
            }
            print(f"---> {self.name} over\n")
        finally:
            # Release lock
            threadLock.release()

@app.get("/run-threads/{num_threads}", response_model=Dict[str, Any])
def run_threads(num_threads: int):
    start_time = time.time()
    threads = []
    results = []

    # Create and start threads
    for i in range(1, num_threads + 1):
        thread = MyThreadClass("Thread#" + str(i) + " ", randint(1, 5))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()
        if thread.result:
            results.append(thread.result)

    total_duration = time.time() - start_time
    return {"threads": results, "total_duration": total_duration}

# Fourth project (similar to second)
@app.get("/execute-2/{thread_number}", response_model=Result)
async def execute_2(thread_number: int):
    result = await run_in_thread2(thread_number)
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
