from google import genai
from dotenv import load_dotenv
import os

load_dotenv()
Gemini_API_KEY = os.getenv("GOOGLE_API_KEY")

# Configuration of the client with API Key
client = genai.Client(api_key=Gemini_API_KEY)

def send_prompt(prompt: str) -> str:
    """
    Sends a message using the modern Gemini client and returns the text.
    Args:
        - prompt (str): The message to send to the Gemini model.
    Returns:
        - response(str): The text response from the Gemini model.
    """
    try:
        # Generation of the response based on the provided prompt
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )

        response = response.text
        
        # Returns only the text of the response
        return response

    except Exception as e:
        print(f"\n[Ocurrió un error en la solicitud hacia Gemini: {str(e)}]")
        return 