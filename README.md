# Grammar-Checker-Backend


## Steps

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/grammar-check-api.git
   cd grammar-check-api
   ```

2. **Set Up Configuration**

   - Create a `config` directory in the project root.
   - Inside the `config` directory, create a file named `api_keys.py`.
   - Add your OpenAI API key to `api_keys.py`:

     ```python
     OPENAI_API_KEY = "your-openai-api-key-here"
     ```

3. **Running the API**

You can run the API locally using Uvicorn, an ASGI server for Python.

```bash
uvicorn main:app --reload
```

- The `--reload` flag enables auto-reloading of the server upon code changes.
- By default, the API will be accessible at `http://127.0.0.1:8000`.

4. **Running the test**
```bash
pytest
```

## API Endpoints

### 1. Submit Grammar Check Request

- **Endpoint:** `/grammar-check`
- **Method:** `POST`
- **Description:** Submits text for grammar checking. The task is processed asynchronously.
- **Request Body:**

  ```json
  {
    "text": "Your text to check goes here."
  }
  ```

- **Response:**

  ```json
  {
    "task_id": "unique-task-id",
    "status": "pending",
    "message": "The task is running in the background."
  }
  ```

### 2. Check Task Status

- **Endpoint:** `/grammar-check/status/{task_id}`
- **Method:** `GET`
- **Description:** Retrieves the status and result of a previously submitted grammar check task.
- **Response:**

  ```json
  {
    "status": "completed",
    "result": [
      {
        "wrong_sentence": "Incorrect sentence.",
        "corrected_sentence": "Corrected sentence.",
        "error_type": "Grammar"
      }
    ],
    "error": null
  }
  ```

## Design Choices

1. **FastAPI Framework:**
   - **Reason:** FastAPI has easy-to-use syntax, and for asynchronous operations, so a good choice for building APIs.

2. **Asynchronous Processing with `asyncio`:**
   - **Reason:** To handle multiple grammar check requests concurrently without blocking the main thread.

3. **Structured Response Models with Pydantic:**
   - **Reason:** Pydantic ensures data validation and serialization, leading to reliable and consistent API responses.

4. **Retry Mechanism for API Calls:**
   - **Reason:** Implementing retries with exponential backoff for OpenAI API calls enhances robustness against transient network or API issues.

## Challenges and Solutions

1. **Asynchronous Task Management:**
   - **Challenge:** Ensuring that grammar check tasks run asynchronously without blocking the main application thread.
   - **Solution:** Utilized `asyncio.create_task` to handle background processing, allowing the API to manage multiple requests efficiently.

2. **Error Handling and Retries:**
   - **Challenge:** Managing potential API errors from OpenAI.
   - **Solution:** Introduced a retry mechanism with exponential backoff to attempt the API call multiple times before failing gracefully, providing clear error messages to the user.

3. **Task Status Tracking:**
   - **Challenge:** Keeping track of the status and results of multiple asynchronous tasks.
   - **Solution:** Maintained an in-memory `tasks` dictionary to store task statuses and results, allowing users to query the status of their submissions effectively.

## Future Improvements

1. **Persistent Task Storage:**
   - **Enhancement:** Integrate a database (e.g., PostgreSQL) to persist task data, ensuring reliability and scalability, especially when deploying the API across multiple instances.

2. **Enhanced Response Models:**
   - **Enhancement:** Provide more detailed grammar check results, including suggestions, explanations, and confidence scores to offer users richer feedback.

3. **Dockerization:**
   - **Enhancement:** Create Docker containers for easier deployment and environment consistency across different platforms.

