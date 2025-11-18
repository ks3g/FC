"""
Configuration Loader for Models

Loads model configurations from YAML file and environment variables.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import re


class ConfigLoader:
    """Loads and manages model configurations."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration loader.

        Args:
            config_path: Path to models.yaml file. If None, uses default location.
        """
        if config_path is None:
            # Default to config/models.yaml in the package
            config_path = Path(__file__).parent / "models.yaml"

        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from YAML file.

        Returns:
            Configuration dictionary
        """
        if not self.config_path.exists():
            print(f"Warning: Config file not found at {self.config_path}")
            print("Using default mock configuration")
            return self._get_default_config()

        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)

            # Resolve environment variables in apiKey fields
            config = self._resolve_env_vars(config)

            return config

        except Exception as e:
            print(f"Error loading config: {e}")
            print("Using default mock configuration")
            return self._get_default_config()

    def _resolve_env_vars(self, config: Dict) -> Dict:
        """
        Resolve ${ENV_VAR} references in configuration.

        Args:
            config: Configuration dictionary

        Returns:
            Configuration with resolved environment variables
        """
        if isinstance(config, dict):
            return {
                key: self._resolve_env_vars(value)
                for key, value in config.items()
            }
        elif isinstance(config, list):
            return [self._resolve_env_vars(item) for item in config]
        elif isinstance(config, str):
            # Match ${VAR_NAME} pattern
            pattern = r'\$\{([^}]+)\}'
            matches = re.findall(pattern, config)
            for var_name in matches:
                env_value = os.getenv(var_name, '')
                config = config.replace(f'${{{var_name}}}', env_value)
            return config
        else:
            return config

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default mock configuration."""
        return {
            'default_model': 'mock',
            'models': {
                'mock': {
                    'title': 'Mock LLM',
                    'provider': 'mock',
                    'model': 'mock-model',
                    'apiBase': '',
                    'apiKey': '',
                    'enabled': True
                }
            },
            'agent_models': {},
            'default_parameters': {
                'temperature': 0.3,
                'max_tokens': 4000
            }
        }

    def get_model_config(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get configuration for a specific model.

        Args:
            model_name: Model name. If None, returns default model.

        Returns:
            Model configuration dictionary
        """
        if model_name is None:
            model_name = self.config.get('default_model', 'mock')

        models = self.config.get('models', {})

        if model_name not in models:
            print(f"Warning: Model '{model_name}' not found in config")
            print("Using mock model")
            return self._get_default_config()['models']['mock']

        model_config = models[model_name].copy()

        # Merge with default parameters
        default_params = self.config.get('default_parameters', {})
        if 'parameters' not in model_config:
            model_config['parameters'] = default_params.copy()

        return model_config

    def get_agent_model_config(self, agent_id: str) -> Dict[str, Any]:
        """
        Get model configuration for a specific agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Model configuration for this agent
        """
        agent_models = self.config.get('agent_models', {})
        model_name = agent_models.get(agent_id)

        return self.get_model_config(model_name)

    def list_available_models(self) -> list:
        """
        List all available models.

        Returns:
            List of model names
        """
        models = self.config.get('models', {})
        return [
            {
                'name': name,
                'title': config.get('title', name),
                'provider': config.get('provider', 'unknown'),
                'model': config.get('model', ''),
                'enabled': config.get('enabled', False),
                'description': config.get('description', '')
            }
            for name, config in models.items()
        ]

    def get_enabled_models(self) -> list:
        """Get list of enabled models."""
        all_models = self.list_available_models()
        return [m for m in all_models if m['enabled']]

    def to_agent_config(self, model_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Convert model config to agent configuration format.

        Args:
            model_name: Model name

        Returns:
            Configuration dict suitable for Agent initialization
        """
        model_config = self.get_model_config(model_name)

        return {
            'llm': {
                'provider': model_config.get('provider', 'mock'),
                'model': model_config.get('model', 'mock-model'),
                'api_key': model_config.get('apiKey', ''),
                'api_base': model_config.get('apiBase', ''),
                'title': model_config.get('title', ''),
                'parameters': model_config.get('parameters', {})
            },
            'enabled': model_config.get('enabled', True)
        }

    def get_performance_settings(self) -> Dict[str, Any]:
        """Get performance settings."""
        return self.config.get('performance', {
            'timeout': 120,
            'retry_attempts': 3,
            'retry_delay': 2
        })

    def get_logging_settings(self) -> Dict[str, Any]:
        """Get logging settings."""
        return self.config.get('logging', {
            'log_requests': True,
            'log_responses': False,
            'log_tokens': True
        })


# Global config loader instance
_config_loader = None


def get_config_loader(config_path: Optional[str] = None) -> ConfigLoader:
    """
    Get global configuration loader instance.

    Args:
        config_path: Optional path to config file

    Returns:
        ConfigLoader instance
    """
    global _config_loader

    if _config_loader is None:
        _config_loader = ConfigLoader(config_path)

    return _config_loader


def load_model_config(model_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to load model configuration.

    Args:
        model_name: Model name or None for default

    Returns:
        Model configuration
    """
    loader = get_config_loader()
    return loader.to_agent_config(model_name)


def load_agent_config(agent_id: str) -> Dict[str, Any]:
    """
    Load configuration for specific agent.

    Args:
        agent_id: Agent identifier

    Returns:
        Agent configuration
    """
    loader = get_config_loader()
    model_config = loader.get_agent_model_config(agent_id)

    return {
        'llm': {
            'provider': model_config.get('provider', 'mock'),
            'model': model_config.get('model', 'mock-model'),
            'api_key': model_config.get('apiKey', ''),
            'api_base': model_config.get('apiBase', ''),
            'title': model_config.get('title', ''),
            'parameters': model_config.get('parameters', {})
        },
        'enabled': model_config.get('enabled', True)
    }
