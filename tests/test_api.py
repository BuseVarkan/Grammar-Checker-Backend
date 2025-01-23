import json
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from app import app

client = TestClient(app)

@pytest.fixture
def mock_openai_response():
    mock_response = [
        {
            "wrong_sentence": "He are going to the store.",
            "corrected_sentence": "He is going to the store.",
            "error_type": "Subject-Verb Agreement"
        },
        {
            "wrong_sentence": "She walk to school everyday.",
            "corrected_sentence": "She walks to school every day.",
            "error_type": "Subject-Verb Agreement"
        }
    ]
    return json.dumps(mock_response)


@patch("app.openai.chat.completions.create")
def test_grammar_check(mock_chat_completion, mock_openai_response):
    mock_chat_completion.return_value = type(
        "MockResponse",
        (object,),
        {
            "choices": [
                type("MockChoice", (object,), {"message": type("MockMessage", (object,), {"content": mock_openai_response})()})
            ]
        }
    )()

    payload = {"text": "He are going to the store. She walk to school everyday."}

    response = client.post("/grammar-check", json=payload)

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    data = response.json()
    assert isinstance(data, list), "Expected a list of grammar suggestions."

    assert len(data) == 3, f"Expected 3 corrections, got {len(data)}."

    assert "wrong_sentence" in data[0], "Missing 'wrong_sentence' in response."
    assert "corrected_sentence" in data[0], "Missing 'corrected_sentence' in response."
    assert "error_type" in data[0], "Missing 'error_type' in response."

    assert data[0]["wrong_sentence"] == "He are going to the store."
    assert data[0]["corrected_sentence"] == "He is going to the store."
    assert data[0]["error_type"] == "Subject-verb agreement"
