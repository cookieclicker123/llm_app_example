import asyncio
import logging
import sys

from backend.app.models.chat import LLMRequest
from backend.app.services.chat_service import handle_chat_stream
from backend.app.utils.ollama_client import create_ollama_stream_func

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    """Runs the interactive terminal chat loop."""
    print("Starting terminal chat with Ollama...")
    print("Type 'quit' or 'exit' to end the session.")

    # Create an instance of the real Ollama streaming function
    try:
        # You might adjust base_url etc. if needed, or load from config later
        ollama_streamer = create_ollama_stream_func()
        logger.info("Ollama stream function created.")
    except Exception as e:
        logger.exception("Failed to create Ollama stream function. Exiting.")
        print(f"Error setting up Ollama client: {e}", file=sys.stderr)
        return

    session_id = "terminal_session_001" # Example session ID

    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.lower() in ["quit", "exit"]:
                print("Exiting chat.")
                break
            if not user_input:
                continue

            request = LLMRequest(
                prompt=user_input,
                session_id=session_id
                # Add model_name or options here if needed
            )

            print("AI: ", end="", flush=True)
            try:
                async for chunk in handle_chat_stream(request, ollama_streamer):
                    print(chunk, end="", flush=True)
                print() # Newline after response stream finishes
            except Exception as e:
                logger.exception(f"Error during chat stream for prompt: '{user_input}'")
                print(f"\nError communicating with LLM: {e}", file=sys.stderr)

        except KeyboardInterrupt:
            print("\nExiting chat due to interrupt.")
            break
        except EOFError: # Handle Ctrl+D
            print("\nExiting chat.")
            break

if __name__ == "__main__":
    # Ensure Ollama service is running before starting
    print("--------------------------------------------------")
    print("IMPORTANT: Make sure the Ollama service is running!")
    print(" (e.g., via Docker Compose or `ollama serve`)")
    print("--------------------------------------------------")
    try:
        asyncio.run(main())
    except Exception as e:
        logger.exception("An unexpected error occurred in the main loop.")
        print(f"\nCritical error: {e}", file=sys.stderr) 