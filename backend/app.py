import asyncio
import httpx
import sys
import json
import logging
import uuid
# Remove direct Redis client import
# import redis.asyncio as redis

# Import settings to get the default model and Redis config
from backend.app.core.config import settings
# Import models needed for handling stream
from backend.app.models.chat import StreamingChunk

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# API Configuration
API_BASE_URL = "http://127.0.0.1:8000"
TOKEN_ENDPOINT = f"{API_BASE_URL}/api/v1/auth/token"
SESSIONS_ENDPOINT = f"{API_BASE_URL}/api/v1/sessions/"
CHAT_ENDPOINT = f"{API_BASE_URL}/api/v1/chat/"
CHAT_STREAM_ENDPOINT = f"{API_BASE_URL}/api/v1/chat/stream"

# Session state (in-memory for the client)
access_token: str | None = None
selected_session_id: str | None = None

# REMOVE old background chat call - history is handled by server
# async def call_chat_endpoint(client: httpx.AsyncClient, payload: dict):
#     ...

# REMOVE old Redis-based session selection
# async def list_and_select_session(redis_conn: redis.Redis) -> str:
#     ...

# --- New API Client Functions --- #

async def login(client: httpx.AsyncClient) -> str | None:
    """Prompts user for credentials and attempts to get an auth token."""
    print("\n--- Login Required ---")
    username = input("Username: ")
    password = input("Password: ") # Consider using getpass for better security
    
    try:
        response = await client.post(
            TOKEN_ENDPOINT, 
            data={"username": username, "password": password}, 
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        response.raise_for_status() # Raise exception for 4xx/5xx errors
        token_data = response.json()
        print("Login successful!")
        return token_data.get("access_token")
    except httpx.HTTPStatusError as e:
        logger.error(f"Login failed: {e.response.status_code} - {e.response.text}")
        print(f"Login failed: {e.response.json().get('detail', e.response.text)}")
        return None
    except httpx.RequestError as e:
        logger.error(f"Could not connect to token endpoint: {e}")
        print("Error: Could not connect to the authentication server.")
        return None
    except Exception as e:
        logger.exception("An unexpected error occurred during login")
        print(f"An unexpected error occurred: {e}")
        return None

async def select_session_from_api(client: httpx.AsyncClient, token: str) -> str | None:
    """Fetches sessions from the API, prompts user to select or start new."""
    session_id = None
    headers = {"Authorization": f"Bearer {token}"}
    existing_sessions = []
    
    try:
        response = await client.get(SESSIONS_ENDPOINT, headers=headers)
        response.raise_for_status()
        sessions_data = response.json()
        # Assuming API returns list of objects with 'session_uuid' and 'last_accessed_at' (or similar for sorting)
        # Sort by last_accessed_at descending (most recent first)
        existing_sessions = sorted(
            sessions_data, 
            key=lambda s: s.get('last_accessed_at', '1970-01-01T00:00:00Z'), 
            reverse=True
        )
    except httpx.HTTPStatusError as e:
        logger.error(f"Failed to list sessions: {e.response.status_code} - {e.response.text}")
        print(f"Error retrieving sessions: {e.response.json().get('detail', e.response.text)}")
        # Allow continuing to create a new session
    except httpx.RequestError as e:
        logger.error(f"Could not connect to sessions endpoint: {e}")
        print("Error: Could not connect to the session server.")
        # Allow continuing to create a new session
    except Exception as e:
        logger.exception("An unexpected error occurred listing sessions")
        print(f"An unexpected error occurred listing sessions: {e}")
        # Allow continuing

    print("\n--- Session Selection ---")
    print("[0] Start new session")
    for i, session in enumerate(existing_sessions):
        # Display more info if available, e.g., title or first message
        print(f"[{i+1}] {session.get('session_uuid')} (Last Access: {session.get('last_accessed_at')})")
    
    while session_id is None:
        try:
            choice = input("Select session index or 0 for new: ")
            choice_idx = int(choice)
            if choice_idx == 0:
                session_id = str(uuid.uuid4()) # Generate UUID V4
                print(f"Starting new session: {session_id}")
            elif 1 <= choice_idx <= len(existing_sessions):
                session_id = existing_sessions[choice_idx - 1]['session_uuid'] # Get the UUID
                print(f"Resuming session: {session_id}")
            else:
                print("Invalid choice, please try again.")
        except (ValueError, IndexError):
            print("Invalid input. Please enter a valid number from the list.")
        except Exception as e:
            logger.error(f"Error during session selection: {e}")
            print("An error occurred. Starting a new session.")
            session_id = str(uuid.uuid4())

    print("-------------------------")
    return session_id

# --- Main Execution Logic --- #

async def main():
    """Runs the interactive terminal chat loop acting as an API client."""
    print("Starting API client terminal chat...")
    print(f"Connecting to API server: {API_BASE_URL}")

    global access_token, selected_session_id

    # Use a single client session for all requests
    async with httpx.AsyncClient(timeout=60.0) as client:
        # --- Login --- #
        access_token = await login(client)
        if not access_token:
            print("Login failed. Exiting.")
            return

        # --- Session Selection --- #
        selected_session_id = await select_session_from_api(client, access_token)
        if not selected_session_id:
            print("No session selected or created. Exiting.")
            return

        print("\nType 'quit' or 'exit' to end the session.")

        # Main chat loop
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
                    "session_id": selected_session_id, # Use the selected UUID
                    "model_name": settings.OLLAMA_DEFAULT_MODEL # Use default model from settings
                }

                # --- Call streaming endpoint (for display) --- #
                print("AI: ", end="", flush=True)
                try:
                    # Add headers to the request
                    headers = {"Authorization": f"Bearer {access_token}"}
                    async with client.stream("POST", CHAT_STREAM_ENDPOINT, json=payload, headers=headers) as response:
                        if response.status_code != 200:
                            # Handle auth errors more gracefully
                            if response.status_code == 401:
                                print("\nAuthentication error (token expired?). Please login again.", file=sys.stderr)
                                access_token = None # Clear token
                                # Re-login could be implemented here by looping back or restarting main
                                print("Restart the client to login again.")
                                break 
                            else:
                                try:
                                    error_detail = await response.aread()
                                    print(f"\nError from stream server ({response.status_code}): {error_detail.decode()}", file=sys.stderr)
                                except Exception:
                                     print(f"\nError from stream server ({response.status_code}). Cannot read detail.", file=sys.stderr)
                            continue
                        
                        # Handle JSON streaming chunks
                        async for line in response.aiter_lines():
                            if line.strip(): # Check if line is not just whitespace
                                try:
                                    chunk_data = json.loads(line)
                                    chunk = StreamingChunk(**chunk_data)
                                    if chunk.content:
                                        print(chunk.content, end="", flush=True)
                                except json.JSONDecodeError:
                                    logger.warning(f"Received non-JSON line from stream: {line}")
                                    # Optionally print the raw line if it's not JSON?
                                    # print(line, end="", flush=True) 
                                except Exception as e:
                                    logger.error(f"Error processing chunk: {e}. Line: {line}")
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
    # Update the example run command to reflect no reload needed for basic testing
    print(" (e.g., `docker compose up -d`)") 
    print(f" This client will connect to {API_BASE_URL}")
    print("---------------------------------------------------------")
    try:
        asyncio.run(main())
    except Exception as e:
        logger.exception("An unexpected error occurred in the client main loop.")
        print(f"\nClient critical error: {e}", file=sys.stderr) 