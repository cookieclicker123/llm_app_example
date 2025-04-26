import asyncio
import httpx
import sys
import json
import logging
import uuid # Import uuid for unique client session

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration - Target the running FastAPI server
API_BASE_URL = "http://127.0.0.1:8000"
CHAT_ENDPOINT = f"{API_BASE_URL}/api/v1/chat/" # Added non-streaming endpoint
CHAT_STREAM_ENDPOINT = f"{API_BASE_URL}/api/v1/chat/stream"

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

async def main():
    """Runs the interactive terminal chat loop acting as an API client."""
    print("Starting API client terminal chat...")
    print(f"Connecting to: {API_BASE_URL}")
    print("Type 'quit' or 'exit' to end the session.")

    # Generate a unique session ID for this client instance
    session_id = f"terminal_client_{uuid.uuid4()}"
    print(f"Session ID: {session_id}")

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
                    # Add model_name or options here if needed
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