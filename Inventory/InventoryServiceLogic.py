from InventoryServiceModel import WorkflowTask, TaskResult
import uuid

def process_task(task: WorkflowTask) -> TaskResult:
    result = {
        "original_data": task.data,
        "processed_flag": True
    }

    return TaskResult(
        task_id=task.id if task.id else str(uuid.uuid4()),
        status="success",
        output=result
    )

print ("InventoryServiceLogic loaded")