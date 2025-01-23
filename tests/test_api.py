import pytest
import os
import time
from fastapi.testclient import TestClient
from app import app, tasks
from uuid import UUID
from config.api_keys import OPENAI_API_KEY

client = TestClient(app)

@pytest.fixture(scope="session")
def openai_api_key():
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY environment variable not set.")

def test_grammar_check_with_actual_openai():

    payload = {
        "text": "He are going to the store. She walk to school everyday."
    }
    
    response = client.post("/grammar-check", json=payload)
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    
    assert "task_id" in data, "Response should contain a task ID."
    assert data["status"] == "pending", "Task status should be 'pending' initially."
    assert "message" in data, "Response should contain a message."
    
    task_id = data["task_id"]
    
    try:
        UUID(task_id, version=4)
    except ValueError:
        pytest.fail("task_id is not a valid UUID.")
    
    max_poll_attempts = 10
    poll_interval = 2  # seconds

    # to ensure that the background task has enough time to complete
    for attempt in range(max_poll_attempts):
        status_response = client.get(f"/grammar-check/status/{task_id}")
        assert status_response.status_code == 200, f"Expected 200, got {status_response.status_code}"
        status_data = status_response.json()
        
        status = status_data.get("status")
        if status == "completed":
            break
        elif status == "failed":
            pytest.fail(f"Task failed with error: {status_data.get('error')}")
        else:
            time.sleep(poll_interval)
    else:
        pytest.fail("Task did not complete within the expected time.")
    
    assert "result" in status_data, "Completed task should contain a 'result'."
    assert isinstance(status_data["result"], list), "Result should be a list of grammar suggestions."
    assert len(status_data["result"]) > 0, "Result list should not be empty."
    
    first_correction = status_data["result"][0]
    assert "wrong_sentence" in first_correction, "Missing 'wrong_sentence' in response."
    assert "corrected_sentence" in first_correction, "Missing 'corrected_sentence' in response."
    assert "error_type" in first_correction, "Missing 'error_type' in response."
    
    assert first_correction["wrong_sentence"] == "He are going to the store."
    assert first_correction["corrected_sentence"] == "He is going to the store."
    assert first_correction["error_type"] == "Subject-verb agreement"

    second_correction = status_data["result"][1]
    assert second_correction["wrong_sentence"] == "She walk to school everyday."
    assert second_correction["corrected_sentence"] == "She walks to school every day."
    assert second_correction["error_type"] == "Subject-verb agreement"

