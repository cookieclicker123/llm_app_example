import asyncio
import httpx
import sys
import json
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration - Target the running FastAPI server
API_BASE_URL = "http://127.0.0.1:8000"
CHAT_STREAM_ENDPOINT = f"{API_BASE_URL}/api/v1/chat/stream"

async def main():
    """Runs the interactive terminal chat loop acting as an API client."""
    print("Starting API client terminal chat...")
    print(f"Connecting to: {API_BASE_URL}")
    print("Type 'quit' or 'exit' to end the session.")

    session_id = "api_client_session_001" # Example session ID for the client

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

                print("AI: ", end="", flush=True)
                try:
                    # Make POST request to the streaming endpoint
                    async with client.stream("POST", CHAT_STREAM_ENDPOINT, json=payload) as response:
                        # Check for non-200 status codes from the server
                        if response.status_code != 200:
                            # Attempt to read error detail if possible
                            error_detail = await response.aread()
                            print(f"\nError from server ({response.status_code}): {error_detail.decode()}", file=sys.stderr)
                            continue # Go to next input prompt
                        
                        # Stream the response chunks
                        async for chunk in response.aiter_text():
                            print(chunk, end="", flush=True)
                        print() # Newline after stream finishes

                except httpx.RequestError as e:
                    logger.error(f"HTTP Request failed: {e}")
                    print(f"\nError connecting to the server at {CHAT_STREAM_ENDPOINT}. Is it running?", file=sys.stderr)
                    print(f"Details: {e}", file=sys.stderr)
                    # Optionally break or wait before retrying
                    await asyncio.sleep(2) # Short delay before next prompt
                except Exception as e:
                    # Catch other potential errors during streaming/processing
                    logger.exception("An error occurred during the chat interaction")
                    print(f"\nAn unexpected error occurred: {e}", file=sys.stderr)

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