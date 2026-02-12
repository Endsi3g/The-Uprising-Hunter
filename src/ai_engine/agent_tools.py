from openai import OpenAI
import os
import importlib.util
import ast
import re
from typing import Optional

class AgenticToolCreator:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key) if api_key else None
        self.tools_dir = os.path.join(os.path.dirname(__file__), "..", "tools_generated")
        os.makedirs(self.tools_dir, exist_ok=True)

    def create_parser_for_site(self, url: str, html_sample: str) -> Optional[str]:
        """
        Generates a Python script to parse a specific clinic website.
        'Permet à ce système de créer ses propres outils de manière intelligente.'
        """
        if not self.client:
            return "Mock parser: logic based on common tags."

        prompt = f"""
        Rédige une fonction Python nommée 'parse_clinic' qui prend une chaîne 'html' en entrée.
        Cette fonction doit extraire :
        1. 'has_faq' (bool)
        2. 'has_online_booking' (bool)
        3. 'has_mobile_optimization' (bool)
        
        URL du site : {url}
        Extrait HTML : {html_sample[:2000]}
        
        Utilise BeautifulSoup. Retourne un dictionnaire.
        Réponds UNIQUEMENT avec le code Python, sans commentaires ni markdown.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            code = response.choices[0].message.content.strip()
            
            # Sanitize domain for safe file path
            domain = re.sub(r'[^\w\-_]', '_', url.split("//")[-1].split("/")[0])
            file_path = os.path.join(self.tools_dir, f"parser_{domain}.py")
            
            # Basic AST validation to prevent immediate RCE from garbage output
            try:
                ast.parse(code)
            except SyntaxError:
                print(f"Generated code has syntax errors, skipping save.")
                return None
            
            if "import os" in code or "import subprocess" in code or "__import__" in code:
                print(f"Generated code contains forbidden imports, skipping save.")
                return None

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)
                
            return file_path
        except Exception as e:
            print(f"Agentic Tool Generation Error: {e}")
            return None

    def execute_generated_tool(self, file_path: str, html: str) -> dict:
        """
        Dynamically loads and runs a generated parser.
        """
        try:
            spec = importlib.util.spec_from_file_location("generated_tool", file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module.parse_clinic(html)
        except Exception as e:
            print(f"Execution Error for {file_path}: {e}")
            return {}
