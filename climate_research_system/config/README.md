# Model Configuration Guide

This directory contains configuration for LLM models used by the climate research agents.

## Quick Start

1. **Edit `models.yaml`** to configure your models
2. **Enable your preferred model** by setting `enabled: true`
3. **Run the system** - agents will automatically use configured models

## Configuration Structure

### Model Block Format

Each model in `models.yaml` follows this structure:

```yaml
model_name:
  title: "Human-readable name"
  provider: "anthropic|openai|ollama"
  model: "model-identifier"
  apiBase: "http://your-endpoint-url"  # Optional, for custom endpoints
  apiKey: "your-api-key"               # Or "${ENV_VAR}" to read from environment
  description: "Model description"
  enabled: true|false
```

### Required Fields

- **title**: Display name for the model
- **provider**: LLM provider (`anthropic`, `openai`, or `ollama`)
- **model**: Model identifier (e.g., `llama3`, `gpt-4`, `claude-3-5-sonnet`)
- **apiBase**: API endpoint URL (important for local models!)
- **apiKey**: Authentication key (can be empty for local models)
- **enabled**: Whether this model is active

## Provider-Specific Configuration

### Ollama (Local Models)

```yaml
local_llama:
  title: "Local Llama 3"
  provider: "ollama"
  model: "llama3"
  apiBase: "http://localhost:11434"  # Ollama default
  apiKey: ""  # No key needed
  enabled: true
```

**Setup:**
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull llama3

# Start Ollama (usually auto-starts)
ollama serve
```

### vLLM Server (OpenAI-Compatible)

```yaml
vllm_server:
  title: "vLLM Llama 3 70B"
  provider: "openai"  # vLLM uses OpenAI-compatible API
  model: "meta-llama/Llama-3-70b"
  apiBase: "http://your-server:8000/v1"
  apiKey: ""  # Add if your server requires auth
  enabled: true
```

**Setup:**
```bash
# Start vLLM server
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Llama-3-70b \
  --port 8000
```

### LM Studio

```yaml
lm_studio:
  title: "LM Studio Local Model"
  provider: "openai"  # LM Studio is OpenAI-compatible
  model: "local-model"
  apiBase: "http://localhost:1234/v1"
  apiKey: ""
  enabled: true
```

**Setup:**
1. Download LM Studio
2. Load a model
3. Start local server (default port: 1234)

### Text Generation WebUI (oobabooga)

```yaml
text_gen_webui:
  title: "Text Generation WebUI"
  provider: "openai"
  model: "your-loaded-model"
  apiBase: "http://localhost:5000/v1"
  apiKey: ""
  enabled: true
```

**Setup:**
1. Start Text Generation WebUI with `--api` flag
2. Load your model
3. Enable OpenAI-compatible API in Extensions

### Custom Research Center Infrastructure

```yaml
custom_internal:
  title: "Internal Research Model"
  provider: "openai"  # For OpenAI-compatible APIs
  model: "your-internal-model"
  apiBase: "http://internal-server:8000/v1"
  apiKey: "${INTERNAL_API_KEY}"  # Read from environment
  enabled: true
```

### Anthropic Claude (Cloud)

```yaml
claude_sonnet:
  title: "Claude 3.5 Sonnet"
  provider: "anthropic"
  model: "claude-3-5-sonnet-20241022"
  apiBase: "https://api.anthropic.com"
  apiKey: "${ANTHROPIC_API_KEY}"
  enabled: true
```

**Setup:**
```bash
export ANTHROPIC_API_KEY='your-key'
```

### OpenAI (Cloud)

```yaml
gpt4_turbo:
  title: "GPT-4 Turbo"
  provider: "openai"
  model: "gpt-4-turbo"
  apiBase: "https://api.openai.com/v1"
  apiKey: "${OPENAI_API_KEY}"
  enabled: true
```

**Setup:**
```bash
export OPENAI_API_KEY='your-key'
```

## Agent-Specific Model Assignment

Assign different models to different agents:

```yaml
agent_models:
  climate_001: "local_llama"          # Fast local model for climate
  emissions_001: "local_llama"        # Same for emissions
  vulnerability_001: "local_mixtral"  # Stronger model for complex analysis
  adaptation_001: "vllm_server"       # Use research center infrastructure
```

If not specified, agents use `default_model`.

## Environment Variables

Use `${VARIABLE_NAME}` to read from environment:

```yaml
apiKey: "${ANTHROPIC_API_KEY}"  # Reads from environment
```

**Supported variables:**
- `${ANTHROPIC_API_KEY}` - Anthropic API key
- `${OPENAI_API_KEY}` - OpenAI API key
- `${YOUR_CUSTOM_VAR}` - Any custom variable

**Set in shell:**
```bash
export ANTHROPIC_API_KEY='sk-ant-...'
export OPENAI_API_KEY='sk-...'
export YOUR_CUSTOM_VAR='value'
```

## Default Parameters

Configure global model parameters:

```yaml
default_parameters:
  temperature: 0.3        # Lower = more factual
  max_tokens: 4000        # Maximum response length
  top_p: 0.9             # Nucleus sampling
  frequency_penalty: 0.0
  presence_penalty: 0.0
```

## Performance Settings

```yaml
performance:
  timeout: 120            # Request timeout (seconds)
  retry_attempts: 3       # Number of retries on failure
  retry_delay: 2          # Delay between retries (seconds)
```

## Logging Configuration

```yaml
logging:
  log_requests: true      # Log API requests
  log_responses: false    # Log full responses (can be large!)
  log_tokens: true        # Log token usage
```

## Usage in Code

### Load Model Config

```python
from config import load_model_config, load_agent_config

# Load default model
config = load_model_config()

# Load specific model
config = load_model_config('local_llama')

# Load config for specific agent
config = load_agent_config('climate_001')
```

### Create Agent with Config

```python
from config import load_agent_config
from research.agents import ClimateDataAgent

# Load configuration for this agent
config = load_agent_config('climate_001')

# Create agent
agent = ClimateDataAgent(agent_id='climate_001', config=config)

# Agent automatically uses configured model!
```

### List Available Models

```python
from config import get_config_loader

loader = get_config_loader()

# List all models
all_models = loader.list_available_models()

# Get only enabled models
enabled = loader.get_enabled_models()

for model in enabled:
    print(f"{model['title']} - {model['provider']}/{model['model']}")
```

## Examples

See `examples/local_model_demo.py` for a complete working example.

```bash
python climate_research_system/examples/local_model_demo.py
```

## Troubleshooting

### "Connection refused" error

**Problem:** Can't connect to local model server
**Solution:**
- Check server is running
- Verify `apiBase` URL is correct
- Check firewall settings

### "Model not found" error

**Problem:** Model isn't available on server
**Solution:**
- For Ollama: `ollama pull model-name`
- For vLLM: Ensure model is loaded
- For LM Studio: Load model in UI first

### "Authentication failed" error

**Problem:** API key is invalid or missing
**Solution:**
- Check `apiKey` is set correctly
- For env vars, verify: `echo $ANTHROPIC_API_KEY`
- For local models, set `apiKey: ""`

### Models not loading from config

**Problem:** System using default instead of config
**Solution:**
- Check `models.yaml` exists in `config/` directory
- Verify YAML syntax is correct
- Check `enabled: true` for your models
- Look for error messages in console

## Best Practices

1. **Use environment variables for keys** - Never commit API keys to git
2. **Enable only needed models** - Reduces clutter
3. **Test locally first** - Use Ollama before deploying to servers
4. **Assign appropriate models** - Stronger models for complex tasks
5. **Monitor token usage** - Check logs for costs
6. **Set reasonable timeouts** - Long enough for local models
7. **Document custom endpoints** - Add descriptions for team clarity

## Security

- **Never commit** `apiKey` values to version control
- Use `${ENV_VAR}` for sensitive values
- Keep `models.yaml` in `.gitignore` if it contains secrets
- For shared configs, use a template: `models.yaml.template`

## Next Steps

1. Edit `models.yaml` for your setup
2. Enable your preferred models
3. Run `examples/local_model_demo.py` to test
4. Start web dashboard: `python climate_research_system/web/app.py`
5. Conduct research with your models!
