from groq import Groq
import json
import requests
from config import Config

class LLMHandler:
    """Handle LLM interactions using Groq (optional feature)"""

    def __init__(self):
        self.provider = Config.LLM_PROVIDER.lower()
        self.client = None
        self.ollama_base_url = Config.OLLAMA_BASE_URL

        # Initialize based on provider
        if self.provider == 'groq':
            if Config.GROQ_API_KEY:
                try:
                    self.client = Groq(api_key=Config.GROQ_API_KEY)
                    print(f"Initialized Groq client with model: {Config.LLM_MODEL}")
                except Exception as e:
                    print(f"Failed to initialize Groq client: {e}")
        elif self.provider == 'ollama':
            # Test Ollama connection
            try:
                response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=5)
                if response.status_code == 200:
                    self.client = 'ollama'  # Use string as flag for Ollama
                    print(f"Connected to Ollama at {self.ollama_base_url}")
                    print(f"Using model: {Config.LLM_MODEL}")
                else:
                    print(f"Ollama server not responding properly: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"Failed to connect to Ollama at {self.ollama_base_url}: {e}")
                print("Make sure Ollama is running with: ollama serve")
        else:
            print(f"Unknown LLM provider: {self.provider}. Use 'groq' or 'ollama'")

        self.model = Config.LLM_MODEL
        self.max_tokens = Config.LLM_MAX_TOKENS

    def is_available(self):
        """Check if LLM is available"""
        return self.client is not None

    def parse_question(self, question):
        """
        Parse user question to extract intent and entities
        Returns: dict with intent, civ_name, unit_name, etc.
        """
        if not self.is_available():
            return self._fallback_parse(question)

        prompt = f"""Extract information from this Age of Empires 2 question.
Return a JSON object with these fields:
- intent: one of [civ_info, unit_stats, unit_counters, compare_civs, bonuses, general]
- civ_name: civilization name if mentioned (or null)
- unit_name: unit name if mentioned (or null)
- civ_name_2: second civilization if comparing (or null)

Question: {question}

Respond with only the JSON object, no other text."""

        try:
            if self.provider == 'groq':
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=200,
                    temperature=0.3
                )
                result = response.choices[0].message.content
            elif self.provider == 'ollama':
                response = requests.post(
                    f"{self.ollama_base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.3,
                            "num_predict": 200
                        }
                    },
                    timeout=120
                )
                response.raise_for_status()
                result = response.json()['response']
            else:
                return self._fallback_parse(question)

            return json.loads(result)
        except Exception as e:
            print(f"LLM parsing error: {e}")
            return self._fallback_parse(question)

    def _fallback_parse(self, question):
        """Fallback parsing without LLM"""
        question_lower = question.lower()

        result = {
            'intent': 'general',
            'civ_name': None,
            'unit_name': None,
            'civ_name_2': None
        }

        # Simple keyword detection
        if 'bonus' in question_lower or 'bonuses' in question_lower:
            result['intent'] = 'bonuses'
        elif 'counter' in question_lower:
            result['intent'] = 'unit_counters'
        elif 'compare' in question_lower or 'vs' in question_lower or 'versus' in question_lower:
            result['intent'] = 'compare_civs'
        elif 'unit' in question_lower or 'stats' in question_lower:
            result['intent'] = 'unit_stats'
        elif 'civ' in question_lower or 'civilization' in question_lower:
            result['intent'] = 'civ_info'

        return result

    def generate_response(self, question, context_data):
        """
        Generate natural language response using retrieved data

        Args:
            question: User's question
            context_data: Retrieved data from JSON files

        Returns:
            Natural language response
        """
        if not self.is_available():
            return self._format_template_response(context_data)

        # Convert context data to string
        context_str = json.dumps(context_data, indent=2)

        prompt = f"""You are an expert on Age of Empires 2: Definitive Edition. 
Answer the user's question using ONLY the provided data. Be concise and helpful.

Data:
{context_str}

Question: {question}

Answer:"""

        try:
            if self.provider == 'groq':
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=self.max_tokens,
                    temperature=0.7
                )
                return response.choices[0].message.content
            elif self.provider == 'ollama':
                response = requests.post(
                    f"{self.ollama_base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "num_predict": self.max_tokens
                        }
                    },
                    timeout=60
                )
                response.raise_for_status()
                return response.json()['response']
            else:
                return self._format_template_response(context_data)
        except Exception as e:
            print(f"LLM generation error: {e}")
            return self._format_template_response(context_data)

    def _format_template_response(self, data):
        """Fallback template-based response formatting"""
        if not data:
            return "I couldn't find any information about that."

        # Simple formatting based on data structure
        if isinstance(data, dict):
            if 'name' in data and 'bonuses' in data:
                # Civilization info
                response = f"**{data['name']}**\n\n"
                if data.get('bonuses'):
                    response += "Bonuses:\n"
                    for bonus in data['bonuses'][:5]:
                        response += f"- {bonus}\n"
                if data.get('team_bonus'):
                    response += f"\nTeam Bonus: {data['team_bonus']}\n"
                if data.get('unique_units'):
                    response += f"\nUnique Units: {', '.join(data['unique_units'])}\n"
                return response
            elif 'unit' in data and ('counters' in data or 'weak_against' in data):
                # Unit counters
                response = f"**{data['unit']}**\n\n"
                if data.get('weak_against'):
                    response += f"Weak against: {', '.join(data['weak_against'])}\n"
                if data.get('strong_against'):
                    response += f"Strong against: {', '.join(data['strong_against'])}\n"
                return response

        return str(data)


if __name__ == '__main__':
    # Test LLM handler
    handler = LLMHandler()

    if handler.is_available():
        print("LLM is available!")

        # Test parsing
        result = handler.parse_question("What are the bonuses for Britons?")
        print("Parsed:", result)
    else:
        print("LLM not available (no API key) - bot will use fallback methods")