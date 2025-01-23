import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from app import app
import time

async def send_grammar_check_request(client, payload):
    response = await client.post("/grammar-check", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    return data["task_id"]

async def poll_task_status(client, task_id, max_poll_attempts=10, poll_interval=2):
    for _ in range(max_poll_attempts):
        status_response = await client.get(f"/grammar-check/status/{task_id}")
        assert status_response.status_code == 200
        status_data = status_response.json()
        if status_data["status"] == "completed":
            return status_data
        elif status_data["status"] == "failed":
            pytest.fail(f"Task {task_id} failed with error: {status_data['error']}")
        await asyncio.sleep(poll_interval)
    pytest.fail(f"Task {task_id} did not complete within the expected time.")

@pytest.mark.asyncio
async def test_concurrent_grammar_checks():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payloads = [
            {"text": "He are going to the store. She walk to school everyday."},
            {"text": "I has a dog. They was happy."},
            {"text": "This are incorrect. Another wrong sentence."},
            {"text": "We was going there. They is playing outside."},
            {"text": "She don't like apples. They doesn't know the answer."}
        ]

        start_time = time.time()

        send_tasks = [send_grammar_check_request(client, payload) for payload in payloads]
        task_ids = await asyncio.gather(*send_tasks)

        poll_tasks = [poll_task_status(client, task_id) for task_id in task_ids]
        results = await asyncio.gather(*poll_tasks)

        end_time = time.time()
        total_duration = end_time - start_time
        print(f"Total duration for all tasks: {total_duration:.2f} seconds")

        assert total_duration < len(payloads) * 2, "Tasks are not running in parallel"

        for result in results:
            assert "result" in result, "Task result missing"
            assert isinstance(result["result"], list), "Result should be a list"
            assert len(result["result"]) > 0, "Result should not be empty"
