# ai_service.py
import requests
from typing import Dict
import json

class AIHelper:
    def __init__(self, model: str = "llama3.2:3b", host: str = "http://localhost:11434"):
        self.model = model
        self.host = host

    def generate_analysis(self, text: str, learning_lang: str, native_lang: str) -> Dict:
        """Generate language analysis using Ollama"""
        try:
            prompt = f"""Analyze this text in {learning_lang}:
            "{text}"

            Provide a helpful analysis in the {native_lang} including:
            1. Translation 
            2. Word breakdown (key vocabulary, and definitions) Include in a table and make sure to include original word in original language for reference.
            3. Grammar points (if any)
            4. Usage notes or cultural context (if relevant)

            Format as JSON with these keys: translation, words, grammar, notes
            Keep explanations clear and beginner-friendly.
            """

            try:
                response = requests.post(
                    f"{self.host}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json"
                    },
                    timeout=30  # Add timeout
                )
                response.raise_for_status()  # Raise exception for bad status codes
                
                result = response.json()
                
                # Ensure we have a valid JSON response
                if isinstance(result, dict) and 'response' in result:
                    analysis = json.loads(result['response'])
                    # Ensure all required keys exist
                    default_analysis = {
                        "translation": "",
                        "words": [],
                        "grammar": [],
                        "notes": []
                    }
                    return {**default_analysis, **analysis}
                else:
                    raise ValueError("Invalid response format from AI service")
                    
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {e}")
                # Return a formatted error response
                return {
                    "translation": "Analysis failed - JSON parsing error",
                    "words": ["Error processing response"],
                    "grammar": [],
                    "notes": [f"Technical error: {str(e)}"]
                }
                
            except requests.exceptions.RequestException as e:
                print(f"Request error: {e}")
                return {
                    "translation": "Analysis failed - Connection error",
                    "words": ["Could not connect to AI service"],
                    "grammar": [],
                    "notes": [f"Connection error: {str(e)}"]
                }
                
        except Exception as e:
            print(f"AI analysis error: {e}")
            return {
                "translation": "Analysis failed",
                "words": [],
                "grammar": [],
                "notes": [f"Error: {str(e)}"]
            }