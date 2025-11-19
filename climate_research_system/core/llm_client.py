"""
LLM Client for Agent Integration

Supports multiple LLM providers:
- Anthropic (Claude)
- OpenAI (GPT)
- Local models (Ollama)
"""

from typing import Dict, List, Optional, Any
from enum import Enum
import json
import os


class LLMProvider(Enum):
    """Supported LLM providers."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    OLLAMA = "ollama"


class EnumJSONEncoder(json.JSONEncoder):
    """JSON encoder that handles Enum types."""
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        if hasattr(obj, '__dict__'):
            return {k: v.value if isinstance(v, Enum) else v
                    for k, v in obj.__dict__.items()
                    if not k.startswith('_')}
        return super().default(obj)


class LLMClient:
    """
    Universal LLM client for agent integration.

    Handles communication with different LLM providers.
    """

    def __init__(
        self,
        provider: str,
        model: str,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        api_type: Optional[str] = None,
        api_version: Optional[str] = None
    ):
        """
        Initialize LLM client.

        Args:
            provider: Provider name (anthropic, openai, ollama)
            model: Model name (e.g., claude-3-5-sonnet, gpt-4)
            api_key: API key (not needed for local models)
            api_base: Custom API base URL (for local models or custom endpoints)
            api_type: API type for Azure OpenAI (openai, azure, azure_ad)
            api_version: API version for Azure OpenAI (e.g., 2024-02-15-preview)
        """
        self.provider = LLMProvider(provider)
        self.model = model
        self.api_key = api_key or os.getenv(f"{provider.upper()}_API_KEY")
        self.api_base = api_base  # Custom endpoint support
        self.api_type = api_type or "openai"  # Default to standard OpenAI
        self.api_version = api_version  # Required for Azure

        # Initialize provider client
        self.client = self._initialize_client()

    def _initialize_client(self):
        """Initialize the appropriate client based on provider."""
        if self.provider == LLMProvider.ANTHROPIC:
            try:
                import anthropic
                client_kwargs = {'api_key': self.api_key}
                if self.api_base:
                    client_kwargs['base_url'] = self.api_base
                return anthropic.Anthropic(**client_kwargs)
            except ImportError:
                print("Warning: anthropic package not installed. Run: pip install anthropic")
                return None

        elif self.provider == LLMProvider.OPENAI:
            try:
                import openai

                # Handle Azure OpenAI separately
                if self.api_type in ['azure', 'azure_ad']:
                    client_kwargs = {'api_key': self.api_key}

                    # Azure requires azure_endpoint instead of base_url
                    if self.api_base:
                        client_kwargs['azure_endpoint'] = self.api_base

                    # Azure requires api_version
                    if self.api_version:
                        client_kwargs['api_version'] = self.api_version

                    return openai.AzureOpenAI(**client_kwargs)

                # Standard OpenAI or OpenAI-compatible APIs
                else:
                    client_kwargs = {'api_key': self.api_key}
                    if self.api_base:
                        client_kwargs['base_url'] = self.api_base
                    return openai.OpenAI(**client_kwargs)

            except ImportError:
                print("Warning: openai package not installed. Run: pip install openai")
                return None

        elif self.provider == LLMProvider.OLLAMA:
            try:
                import ollama
                # Ollama client with custom host if specified
                if self.api_base:
                    # Ollama uses 'host' parameter
                    return ollama.Client(host=self.api_base)
                return ollama
            except ImportError:
                print("Warning: ollama package not installed. Run: pip install ollama")
                return None

        return None

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4000,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Generate response from LLM.

        Args:
            prompt: User prompt
            system_prompt: System prompt (instructions)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Dict with 'content', 'model', 'tokens_used'
        """
        if not self.client:
            return {
                'content': '[LLM client not available - API package not installed]',
                'model': self.model,
                'tokens_used': 0,
                'error': 'Client not initialized'
            }

        try:
            if self.provider == LLMProvider.ANTHROPIC:
                return self._generate_anthropic(prompt, system_prompt, max_tokens, temperature)

            elif self.provider == LLMProvider.OPENAI:
                return self._generate_openai(prompt, system_prompt, max_tokens, temperature)

            elif self.provider == LLMProvider.OLLAMA:
                return self._generate_ollama(prompt, system_prompt, max_tokens, temperature)

        except Exception as e:
            return {
                'content': f'[LLM Error: {str(e)}]',
                'model': self.model,
                'tokens_used': 0,
                'error': str(e)
            }

    def _generate_anthropic(self, prompt, system_prompt, max_tokens, temperature):
        """Generate using Anthropic Claude."""
        messages = [{"role": "user", "content": prompt}]

        kwargs = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        response = self.client.messages.create(**kwargs)

        return {
            'content': response.content[0].text,
            'model': self.model,
            'tokens_used': response.usage.input_tokens + response.usage.output_tokens,
            'provider': 'anthropic'
        }

    def _generate_openai(self, prompt, system_prompt, max_tokens, temperature):
        """Generate using OpenAI GPT."""
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )

        return {
            'content': response.choices[0].message.content,
            'model': self.model,
            'tokens_used': response.usage.total_tokens,
            'provider': 'openai'
        }

    def _generate_ollama(self, prompt, system_prompt, max_tokens, temperature):
        """Generate using Ollama (local)."""
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        # Check if client is an Ollama Client instance or module
        if hasattr(self.client, 'generate'):
            # Client instance
            response = self.client.generate(
                model=self.model,
                prompt=full_prompt,
                options={
                    'temperature': temperature,
                    'num_predict': max_tokens
                }
            )
        else:
            # Module (default ollama)
            import ollama as ollama_module
            response = ollama_module.generate(
                model=self.model,
                prompt=full_prompt,
                options={
                    'temperature': temperature,
                    'num_predict': max_tokens
                }
            )

        return {
            'content': response['response'],
            'model': self.model,
            'tokens_used': response.get('eval_count', 0),
            'provider': 'ollama'
        }

    def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate structured JSON output.

        Args:
            prompt: User prompt
            schema: JSON schema for expected output
            system_prompt: System prompt

        Returns:
            Parsed JSON response
        """
        schema_str = json.dumps(schema, indent=2, cls=EnumJSONEncoder)

        enhanced_prompt = f"""
{prompt}

Please respond with valid JSON matching this schema:
{schema_str}

Only return the JSON, no other text.
"""

        response = self.generate(enhanced_prompt, system_prompt)

        try:
            # Extract JSON from response
            content = response['content']

            # Try to find JSON in response
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            elif '```' in content:
                content = content.split('```')[1].split('```')[0]

            parsed = json.loads(content.strip())
            response['parsed'] = parsed

        except json.JSONDecodeError as e:
            response['parsed'] = None
            response['parse_error'] = str(e)

        return response


class MockLLMClient:
    """
    Mock LLM client for testing without API keys.
    Returns simulated responses.
    """

    def __init__(self, provider: str = "mock", model: str = "mock-model", api_key: str = None):
        self.provider = provider
        self.model = model
        self.api_key = api_key

    def generate(self, prompt: str, system_prompt: str = None, max_tokens: int = 4000, temperature: float = 0.7):
        """Return mock response."""
        return {
            'content': self._generate_mock_response(prompt),
            'model': self.model,
            'tokens_used': 100,
            'provider': 'mock'
        }

    def _generate_mock_response(self, prompt: str) -> str:
        """Generate contextual mock response based on prompt."""
        prompt_lower = prompt.lower()

        if 'climate' in prompt_lower or 'temperature' in prompt_lower:
            return """Based on the climate data analysis:

**Temperature Trends:**
- Average temperature: 10-15°C with warming trend of +1.5°C over past 30 years
- Increasing frequency of heat waves (5-10 per year)

**Precipitation:**
- Annual precipitation: 600-800mm
- More intense rainfall events, longer dry periods

**Key Risks:**
- Urban heat island effect
- Increased flooding risk
- Water stress during summer months

**Recommendations:**
- Expand green infrastructure
- Improve stormwater management
- Develop heat action plans"""

        elif 'emission' in prompt_lower or 'carbon' in prompt_lower:
            return """Emissions Analysis:

**Total GHG Emissions:** 5.2 million tons CO2e/year

**Breakdown by Sector:**
- Transport: 40% (2.1M tons)
- Buildings: 35% (1.8M tons)
- Industry: 15% (0.8M tons)
- Waste: 10% (0.5M tons)

**Per Capita:** 6.5 tons CO2e/person/year

**Trends:** 15% reduction since 2010 baseline

**Recommendations:**
- Accelerate transport electrification
- Retrofit building stock
- Expand renewable energy"""

        elif 'vulnerabilit' in prompt_lower or 'risk' in prompt_lower:
            return """Climate Vulnerability Assessment:

**High Risk Areas:**
- Flood-prone zones along rivers (affecting 25,000 residents)
- Urban heat islands in dense neighborhoods
- Aging infrastructure vulnerable to extreme weather

**Vulnerable Populations:**
- Elderly (15% of population)
- Low-income communities (limited adaptation capacity)
- Outdoor workers

**Critical Infrastructure at Risk:**
- Power grid during heat waves
- Transportation during floods
- Water supply during droughts

**Priority Actions:**
- Early warning systems
- Cooling centers
- Infrastructure upgrades"""

        else:
            return """[Mock LLM Response]

This is a simulated response for testing purposes.

To get real AI-powered analysis, configure API keys:
- Anthropic Claude: Set ANTHROPIC_API_KEY
- OpenAI GPT: Set OPENAI_API_KEY
- Ollama: Install locally

The agent would analyze the provided data and generate detailed insights."""

    def generate_structured(self, prompt: str, schema: Dict, system_prompt: str = None):
        """Return mock structured response."""
        response = self.generate(prompt, system_prompt)

        # Generate mock structured data
        response['parsed'] = {
            'summary': response['content'][:200],
            'key_findings': [
                'Finding 1 from analysis',
                'Finding 2 from analysis',
                'Finding 3 from analysis'
            ],
            'confidence': 0.75,
            'data_quality': 'medium'
        }

        return response
