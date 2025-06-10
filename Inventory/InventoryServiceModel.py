from pydantic import BaseModel, Field
from typing import List, Optional
import uuid

class WorkflowTask(BaseModel):
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str
    data: dict

class WorkflowRequest(BaseModel):
    user_id: str
    tasks: List[WorkflowTask]

class TaskResult(BaseModel):
    task_id: str
    status: str
    output: dict

class WorkflowResponse(BaseModel):
    user_id: str
    results: List[TaskResult]

print("InventoryServiceModel loaded")