import asyncio
import httpx
import sys
import json
import logging
import uuid
import redis.asyncio as redis # Import Redis client

# Import settings to get the default model and Redis config
from backend.app.core.config import settings

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
API_BASE_URL = "http://127.0.0.1:8000"
CHAT_ENDPOINT = f"{API_BASE_URL}/api/v1/chat/"
CHAT_STREAM_ENDPOINT = f"{API_BASE_URL}/api/v1/chat/stream"
REDIS_HOST = settings.REDIS_HOST # Use host from settings (likely localhost for client)
REDIS_PORT = settings.REDIS_PORT
REDIS_DB = settings.REDIS_DB
SESSION_KEY_PREFIX = "session:" # Should match the prefix in history_crud.py

async def call_chat_endpoint(client: httpx.AsyncClient, payload: dict):
    """Calls the non-streaming chat endpoint to log the request/response.
       Handles errors internally and logs them.
    """
    try:
        response = await client.post(CHAT_ENDPOINT, json=payload)
        if response.status_code != 200:
            try:
                error_detail = response.json()
            except json.JSONDecodeError:
                error_detail = await response.aread()
                error_detail = error_detail.decode()
            logger.error(f"Error calling chat endpoint ({response.status_code}): {error_detail}")
        else:
            # Log success, response content is implicitly saved by the server
            response_data = response.json()
            logger.info(f"Successfully called chat endpoint for saving. Response ID: {response_data.get('response_id')}")
    except httpx.RequestError as e:
        logger.error(f"HTTP Request failed for chat endpoint: {e}")
    except Exception as e:
        logger.exception("An unexpected error occurred calling chat endpoint")

async def list_and_select_session(redis_conn: redis.Redis) -> str:
    """Lists existing sessions from Redis and prompts user to select or start new."""
    session_id = None
    existing_sessions = []
    try:
        keys = await redis_conn.keys(f"{SESSION_KEY_PREFIX}*")
        existing_sessions = sorted([key.decode().replace(SESSION_KEY_PREFIX, "") for key in keys])
    except Exception as e:
        logger.warning(f"Could not connect to Redis to list sessions: {e}")
        print("Warning: Could not retrieve existing sessions from Redis.")

    print("\n--- Session Selection ---")
    print("[0] Start new session")
    for i, session in enumerate(existing_sessions):
        print(f"[{i+1}] {session}")
    
    while session_id is None:
        try:
            choice = input("Select session index or 0 for new: ")
            choice_idx = int(choice)
            if choice_idx == 0:
                session_id = f"terminal_client_{uuid.uuid4()}"
                print(f"Starting new session: {session_id}")
            elif 1 <= choice_idx <= len(existing_sessions):
                session_id = existing_sessions[choice_idx - 1]
                print(f"Resuming session: {session_id}")
            else:
                print("Invalid choice, please try again.")
        except ValueError:
            print("Invalid input. Please enter a number.")
        except Exception as e:
            logger.error(f"Error during session selection: {e}")
            print("An error occurred. Starting a new session.")
            session_id = f"terminal_client_{uuid.uuid4()}"

    print("-------------------------")
    return session_id

async def main():
    """Runs the interactive terminal chat loop acting as an API client."""
    print("Starting API client terminal chat...")
    print(f"Connecting to API server: {API_BASE_URL}")

    redis_conn = None
    try:
        # Connect to Redis
        redis_conn = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
        await redis_conn.ping() # Test connection
        print(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
        # Select or start session
        session_id = await list_and_select_session(redis_conn)
    except Exception as e:
        logger.error(f"Failed to connect to Redis or select session: {e}")
        print("\nError connecting to Redis. Starting without session history features.")
        session_id = f"terminal_client_{uuid.uuid4()}"
        print(f"Starting new session: {session_id}")
        print("-------------------------")
        if redis_conn:
            await redis_conn.close() # Close if connection was partial
            redis_conn = None

    print("Type 'quit' or 'exit' to end the session.")
    # print(f"Using Session ID: {session_id}") # No longer needed, printed during selection

    # Use httpx.AsyncClient for making requests
    async with httpx.AsyncClient(timeout=60.0) as client:
        while True:
            try:
                user_input = input("\nYou: ")
                if user_input.lower() in ["quit", "exit"]:
                    print("Exiting chat.")
                    break
                if not user_input:
                    continue

                # Prepare request payload matching LLMRequest model
                payload = {
                    "prompt": user_input,
                    "session_id": session_id,
                    "model_name": settings.OLLAMA_DEFAULT_MODEL # Use default model from settings
                }

                # --- Call non-streaming endpoint in the background --- #
                # Create a task to run the saving call concurrently
                # We don't await it here, letting it run independently
                save_task = asyncio.create_task(
                    call_chat_endpoint(client, payload),
                    name=f"save_task_{payload['prompt'][:10]}" # Optional name for debugging
                )
                # Add callback to log if the background task fails (optional but good practice)
                save_task.add_done_callback(
                    lambda t: logger.error(f"Background save task failed: {t.exception()}") if t.exception() else None
                )
                # -------------------------------------------------------- #

                # --- Call streaming endpoint (for display) --- #
                print("AI: ", end="", flush=True)
                try:
                    async with client.stream("POST", CHAT_STREAM_ENDPOINT, json=payload) as response:
                        if response.status_code != 200:
                            error_detail = await response.aread()
                            print(f"\nError from stream server ({response.status_code}): {error_detail.decode()}", file=sys.stderr)
                            continue
                        
                        async for chunk in response.aiter_text():
                            print(chunk, end="", flush=True)
                        print() # Newline after stream finishes

                except httpx.RequestError as e:
                    logger.error(f"HTTP Request failed for stream endpoint: {e}")
                    print(f"\nError connecting to the stream server at {CHAT_STREAM_ENDPOINT}. Is it running?", file=sys.stderr)
                    await asyncio.sleep(2)
                except Exception as e:
                    logger.exception("An error occurred during the stream interaction")
                    print(f"\nAn unexpected error occurred during stream: {e}", file=sys.stderr)
                # ------------------------------------------------- #

            except KeyboardInterrupt:
                print("\nExiting chat due to interrupt.")
                break
            except EOFError: # Handle Ctrl+D
                print("\nExiting chat.")
                break

    # Close Redis connection if open
    if redis_conn:
        await redis_conn.close()
        logger.info("Closed Redis connection.")

if __name__ == "__main__":
    print("---------------------------------------------------------")
    print("IMPORTANT: Make sure the FastAPI server is running!")
    print(" (e.g., `uvicorn backend.app.main:app --reload`)")
    print(f" This client will connect to {API_BASE_URL}")
    print("---------------------------------------------------------")
    try:
        asyncio.run(main())
    except Exception as e:
        logger.exception("An unexpected error occurred in the client main loop.")
        print(f"\nClient critical error: {e}", file=sys.stderr) 