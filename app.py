import asyncio
import json
import uuid
from config.api_keys import OPENAI_API_KEY
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List
import openai
from prompts.prompt import system_prompt

app = FastAPI(title="Grammar Check API", description="API to check grammar using LLM.")

client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Request class
class GrammarCheckRequest(BaseModel):
    text: str

# Response class
class GrammarCheckResponse(BaseModel):
    wrong_sentence: str
    corrected_sentence: str
    error_type: str

# Task storage
tasks: Dict[str, Dict] = {}

@app.post("/grammar-check", response_model=dict)
async def grammar_check(request: GrammarCheckRequest, background_tasks: BackgroundTasks):
    text = request.text
    if not text.strip():
        raise HTTPException(status_code=400, detail="Input text cannot be empty.")

    try:
        task_id = str(uuid.uuid4())

        tasks[task_id] = {"status": "pending", "result": None, "error": None}

        asyncio.create_task(run_grammar_check_task(task_id, text))

        print({"task_id": task_id, "status": "pending", "message": "The task is running in the background."})
        return {"task_id": task_id, "status": "pending", "message": "The task is running in the background."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing text: {str(e)}")
        
async def run_grammar_check_task(task_id: str, text: str):
    try:
        result = await process_text(text)

        tasks[task_id]["status"] = "completed"
        tasks[task_id]["result"] = result

        print(f"Task {task_id} completed.")
        print(result)
    except Exception as e:
        tasks[task_id]["status"] = "failed"
        tasks[task_id]["error"] = str(e)


@app.get("/grammar-check/status/{task_id}", response_model=dict)
async def get_task_status(task_id: str):
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task ID not found.")

    print(tasks[task_id])
    return tasks[task_id]

async def process_text(text: str) -> List[GrammarCheckResponse]:
    attempt = 0
    sleep_duration = 1

    while True:
        try:
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt()},
                    {"role": "user", "content": text}
                ],
                temperature=0.0
            )

            response_text = completion.choices[0].message.content
            processed_result = parse_llm_response(response_text)
            return processed_result

        except openai.APIError as e:
            attempt += 1
            if attempt >= 3:
                raise RuntimeError(f"OpenAI API error after {attempt} attempts: {str(e)}")

            await asyncio.sleep(sleep_duration)
            sleep_duration *= 2

        except ValueError as e:
            raise RuntimeError(f"Invalid response format: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error: {str(e)}")


def parse_llm_response(response_text: str) -> List[GrammarCheckResponse]:
    try:
        response_json = json.loads(response_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM response is not valid JSON. Parsing error: {e}")

    if not isinstance(response_json, list):
        raise ValueError("LLM response should be a JSON list.")

    llm_result: List[GrammarCheckResponse] = []
    for idx, item in enumerate(response_json):
        if not isinstance(item, dict):
            raise ValueError(f"Item at index {idx} is not an object: {item}")

        llm_result.append(
            GrammarCheckResponse(
                wrong_sentence=item.get("wrong_sentence", "Unknown"),
                corrected_sentence=item.get("corrected_sentence", "Unknown"),
                error_type=item.get("error_type", "Unknown")
            )
        )

    return llm_result
