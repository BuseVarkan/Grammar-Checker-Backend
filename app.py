import json
from config.api_keys import OPENAI_API_KEY
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List
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

@app.post("/grammar-check", response_model=List[GrammarCheckResponse])
async def grammar_check(request: GrammarCheckRequest, background_tasks: BackgroundTasks):
    text = request.text
    if not text.strip():
        raise HTTPException(status_code=400, detail="Input text cannot be empty.")

    try:
        result = await process_text(text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing text: {str(e)}")

async def process_text(text: str) -> List[GrammarCheckResponse]:
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

    except openai.error.OpenAIError as e:
        raise RuntimeError(f"OpenAI API error: {str(e)}")
    except ValueError as e:
        raise RuntimeError(f"Invalid response format: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error: {str(e)}")

def parse_llm_response(response_text: str) -> List[GrammarCheckResponse]:
    try:
        llm_result = []
        response_json = json.loads(response_text)

        if not isinstance(response_json, list):
            raise ValueError("LLM response should be a JSON list.")

        for item in response_json:
            llm_result.append(
                GrammarCheckResponse(
                    wrong_sentence=item.get("wrong_sentence", "Unknown"),
                    corrected_sentence=item.get("corrected_sentence", "Unknown"),
                    error_type=item.get("error_type", "Unknown")
                )
            )
        return llm_result

    except (SyntaxError, TypeError, ValueError) as e:
        raise ValueError(f"Failed to parse LLM response: {str(e)}")
