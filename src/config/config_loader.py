import os
import json
from pathlib import Path

DEFAULT_CONFIG = {
    "llm": {
        "provider": "gemini",
        "ollama_url": "http://localhost:11434",
        "models": {
            "translator": "gemma-4-26b-a4b-it",
            "processor": "gemma-4-26b-a4b-it",
            "reporter": "gemma-4-26b-a4b-it",
            "company_profile": "gemma-4-31b-it",
            "financial_audit": "gemma-4-31b-it",
            "report_synthesizer": "gemma-4-31b-it"
        }
    },
    "rag": {
        "searxng_url": "http://localhost:8080",
        "max_iterations": 3,
        "similarity_threshold": 0.3,
        "num_search_results": 5,
        "max_content_characters": 30000
    }
}

class Config:
    _config = None

    @classmethod
    def get_all(cls):
        if cls._config is None:
            config_path = Path(__file__).resolve().parents[2] / 'config.json'
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        user_config = json.load(f)
                        # Deep merge defaults with user config
                        cls._config = cls._merge_configs(DEFAULT_CONFIG, user_config)
                except Exception as e:
                    print(f"Warning: Failed to load config.json ({e}). Using default settings.")
                    cls._config = DEFAULT_CONFIG
            else:
                cls._config = DEFAULT_CONFIG
        return cls._config

    @classmethod
    def get(cls, section, key, default=None):
        cfg = cls.get_all()
        return cfg.get(section, {}).get(key, default)

    @classmethod
    def _merge_configs(cls, default, user):
        merged = {}
        for key in default:
            if key in user:
                if isinstance(default[key], dict) and isinstance(user[key], dict):
                    merged[key] = cls._merge_configs(default[key], user[key])
                else:
                    merged[key] = user[key]
            else:
                merged[key] = default[key]
        # Also copy over any keys in user that are not in default to allow custom options
        for key in user:
            if key not in merged:
                merged[key] = user[key]
        return merged
