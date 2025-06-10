from fastapi import FastAPI, HTTPException
from InventoryServiceModel import WorkflowRequest, WorkflowResponse
from InventoryServiceLogic import process_task

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = FastAPI(title="Kitchen inventorization service")

@app.post("/process", response_model=WorkflowResponse)
async def process_workflow(request: WorkflowRequest):
    try:
        results = [process_task(task) for task in request.tasks]
        return WorkflowResponse(user_id=request.user_id, results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))