import os
import json
import anthropic
import openai
from dotenv import load_dotenv

load_dotenv()

with open(os.path.join(os.path.dirname(__file__), 'models.json')) as f:
    MODEL_REGISTRY = json.load(f)

def get_available_providers():
    available = []
    for provider_id, config in MODEL_REGISTRY['providers'].items():
        key = os.getenv(config['env_key'], '')
        if key and key not in ('your_anthropic_key_here', 'your_openai_key_here'):
            available.append(provider_id)
    return available

def get_provider_for_model(model_id):
    for provider_id, config in MODEL_REGISTRY['providers'].items():
        for model in config['models']:
            if model['id'] == model_id:
                return provider_id
    return None

def call_llm(system_prompt, messages, model_id=None, max_tokens=1000):
    if model_id is None:
        model_id = os.getenv('DEFAULT_AGENT_MODEL', 'claude-sonnet-4-6')
    provider = get_provider_for_model(model_id)
    if provider is None:
        raise ValueError(f"Unknown model_id: {model_id}")
    if provider == 'anthropic':
        client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        response = client.messages.create(
            model=model_id,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages
        )
        return {"text": response.content[0].text, "model": model_id, "provider": "anthropic"}
    elif provider == 'openai':
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        openai_messages = [{"role": "system", "content": system_prompt}] + messages
        if model_id.startswith('o1'):
            first_user = next((m for m in messages if m['role'] == 'user'), None)
            if first_user:
                openai_messages = messages.copy()
                openai_messages[0] = {
                    "role": "user",
                    "content": f"{system_prompt}\n\n{first_user['content']}"
                }
        kwargs = {"model": model_id, "messages": openai_messages}
        if model_id.startswith('o1'):
            kwargs["max_completion_tokens"] = max_tokens
        else:
            kwargs["max_tokens"] = max_tokens
        response = client.chat.completions.create(**kwargs)
        return {"text": response.choices[0].message.content, "model": model_id, "provider": "openai"}
    raise ValueError(f"Unknown provider: {provider}")

def get_models_for_frontend():
    available_providers = get_available_providers()
    result = {"providers": {}}
    for provider_id in available_providers:
        result["providers"][provider_id] = MODEL_REGISTRY["providers"][provider_id]
    return result
