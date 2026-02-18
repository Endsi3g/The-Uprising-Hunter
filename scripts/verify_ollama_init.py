import os
import sys

# Add project root to path
sys.path.append(os.getcwd())

# Mock secrets manager to avoid import errors if not set up
import types
sys.modules['src.admin.secrets_manager'] = types.ModuleType('src.admin.secrets_manager')
sys.modules['src.admin.secrets_manager'].secrets_manager = types.SimpleNamespace()
sys.modules['src.admin.secrets_manager'].secrets_manager.resolve_secret = lambda x, y: "fake-key"

from src.ai_engine.generator import MessageGenerator

def test_ollama_init():
    print("Testing Ollama Initialization...")
    os.environ['LLM_PROVIDER'] = 'ollama'
    os.environ['LLM_MODEL'] = 'tinyllama'
    
    generator = MessageGenerator()
    
    if generator.provider != 'ollama':
        print("FAIL: Provider not set to ollama")
        return
        
    if generator.client.base_url != "http://localhost:11434/v1/":
        print(f"FAIL: Unexpected base_url: {generator.client.base_url}")
        return
        
    print("SUCCESS: MessageGenerator initialized with Ollama settings.")
    print(f"Provider: {generator.provider}")
    print(f"Model: {generator.model_name}")
    print(f"Base URL: {generator.client.base_url}")

if __name__ == "__main__":
    test_ollama_init()
