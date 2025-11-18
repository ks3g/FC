

# LLM Configuration Guide

All agents in the Climate Research System are now LLM-powered! This guide shows you how to configure them.

## Quick Start

**Option 1: Use Mock LLM (No API Key Needed)**
- Agents work out of the box with simulated responses
- Perfect for testing the system
- No costs, no API keys required

**Option 2: Use Real LLM (Recommended for Production)**
- Get intelligent, context-aware climate analysis
- Choose from Anthropic Claude, OpenAI GPT, or local Ollama

---

## Supported LLM Providers

### 1. **Anthropic Claude** (Recommended)
Best for detailed climate analysis with long-context understanding.

**Models:**
- `claude-3-5-sonnet-20241022` - Best balance (recommended)
- `claude-3-5-haiku-20241022` - Faster, cheaper
- `claude-3-opus-20240229` - Most capable

**Setup:**
```bash
# Install
pip install anthropic

# Set API key
export ANTHROPIC_API_KEY='your-api-key-here'
```

**Get API Key:** https://console.anthropic.com/

### 2. **OpenAI GPT**
Alternative option with good performance.

**Models:**
- `gpt-4-turbo` - Best quality
- `gpt-4` - Very capable
- `gpt-3.5-turbo` - Fast and cheap

**Setup:**
```bash
# Install
pip install openai

# Set API key
export OPENAI_API_KEY='your-api-key-here'
```

**Get API Key:** https://platform.openai.com/api-keys

### 3. **Ollama** (Local Models)
Run models locally, no API key needed, completely private.

**Models:**
- `llama3` - Good general purpose
- `mixtral` - Strong reasoning
- `phi3` - Lightweight

**Setup:**
```bash
# Install Ollama from https://ollama.ai
# Then install Python client
pip install ollama

# Pull a model
ollama pull llama3
```

---

## Agent Configuration

### Method 1: Environment Variables (Easiest)

Set your API key once:

```bash
# For Anthropic
export ANTHROPIC_API_KEY='sk-ant-...'

# For OpenAI
export OPENAI_API_KEY='sk-...'

# For Ollama (no key needed, just install)
# ollama serve
```

Then agents will automatically use it!

### Method 2: Configuration Dict

Pass config when creating agents:

```python
from research.agents import ClimateDataAgent, EmissionsAgent

# Anthropic Claude
climate_agent = ClimateDataAgent(
    agent_id="climate_001",
    config={
        'llm': {
            'provider': 'anthropic',
            'model': 'claude-3-5-sonnet-20241022',
            'api_key': 'your-api-key'  # Optional if set in environment
        },
        'enabled': True
    }
)

# OpenAI GPT
emissions_agent = EmissionsAgent(
    agent_id="emissions_001",
    config={
        'llm': {
            'provider': 'openai',
            'model': 'gpt-4-turbo',
            'api_key': 'your-api-key'
        },
        'enabled': True
    }
)

# Ollama (local)
vulnerability_agent = VulnerabilityAgent(
    agent_id="vulnerability_001",
    config={
        'llm': {
            'provider': 'ollama',
            'model': 'llama3'
            # No API key needed
        },
        'enabled': True
    }
)
```

### Method 3: No Configuration (Mock Mode)

Don't configure anything - agents use MockLLMClient:

```python
# This works without API keys
agent = ClimateDataAgent()

# Uses simulated LLM responses
result = agent.execute({'city': 'Paris', 'country': 'France'})
```

---

## Available Agents

### 1. **ClimateDataAgent**
Analyzes temperature, precipitation, extreme events, climate trends.

**Prompt Focus:**
- Historical climate data analysis
- Temperature and precipitation trends
- Extreme weather patterns
- Climate change impacts
- Adaptation recommendations

### 2. **EmissionsAgent**
Analyzes GHG emissions by sector, trends, reduction targets.

**Prompt Focus:**
- Emissions inventory (transport, buildings, industry, waste)
- Per capita emissions
- Mitigation strategies
- Carbon reduction pathways

### 3. **VulnerabilityAgent**
Assesses climate risks, vulnerable populations, infrastructure exposure.

**Prompt Focus:**
- Flood, heat, drought, storm risks
- Vulnerable demographics
- Critical infrastructure
- Risk assessment and prioritization

### 4. **AdaptationAgent**
Evaluates climate action plans, green infrastructure, policies.

**Prompt Focus:**
- Climate action plans
- Nature-based solutions
- Adaptation measures
- Policy and governance
- Implementation status

---

## Example Usage

### Complete Research with All Agents

```python
from research.orchestrator import ResearchOrchestrator
from research.agents import (
    ClimateDataAgent,
    EmissionsAgent,
    VulnerabilityAgent,
    AdaptationAgent
)

# Initialize orchestrator
orchestrator = ResearchOrchestrator()

# Create agents with LLM config
llm_config = {
    'llm': {
        'provider': 'anthropic',  # or 'openai', 'ollama'
        'model': 'claude-3-5-sonnet-20241022'
        # API key from environment variable
    },
    'enabled': True
}

# Register all agents
orchestrator.register_agent(ClimateDataAgent("climate_001", llm_config))
orchestrator.register_agent(EmissionsAgent("emissions_001", llm_config))
orchestrator.register_agent(VulnerabilityAgent("vulnerability_001", llm_config))
orchestrator.register_agent(AdaptationAgent("adaptation_001", llm_config))

# Run research - all 4 agents analyze the city
results = orchestrator.research_city("Copenhagen", "Denmark")

# Access LLM analysis from each agent
print("Climate Analysis:")
print(results['agent_results']['climate_001']['llm_analysis'])

print("\nEmissions Analysis:")
print(results['agent_results']['emissions_001']['llm_analysis'])

print("\nVulnerability Assessment:")
print(results['agent_results']['vulnerability_001']['llm_analysis'])

print("\nAdaptation Strategies:")
print(results['agent_results']['adaptation_001']['llm_analysis'])
```

---

## Cost Considerations

### Anthropic Claude Pricing (as of 2024)
- **Claude 3.5 Sonnet:** ~$3 per million input tokens, ~$15 per million output tokens
- **Typical research request:** 2,000-4,000 tokens (input + output)
- **Cost per city research:** $0.05 - $0.10 per agent
- **Full research (4 agents):** ~$0.20 - $0.40

### OpenAI GPT Pricing
- **GPT-4 Turbo:** ~$10 per million input tokens, ~$30 per million output tokens
- **Typical research request:** Similar costs to Claude

### Ollama (Local)
- **FREE** - runs on your machine
- Requires decent GPU for best performance
- Completely private

### Mock Mode
- **FREE** - no API calls
- Good for development and testing
- Returns simulated but contextually appropriate responses

---

## Tips for Best Results

### 1. **Model Selection**
- **Research depth:** Claude 3.5 Sonnet or GPT-4
- **Speed/cost:** Claude 3.5 Haiku or GPT-3.5
- **Privacy:** Ollama local models

### 2. **Temperature Settings**
Already optimized in agents (0.3 for factual analysis)

### 3. **Token Management**
Agents use ~1,000-2,000 tokens per analysis. Monitor usage in results:
```python
print(f"Tokens used: {results['agent_results']['climate_001']['tokens_used']}")
```

### 4. **Rate Limits**
- Anthropic: 50,000 tokens/minute (default)
- OpenAI: 90,000 tokens/minute (tier 1)
- Research 4 cities simultaneously without issues

### 5. **Caching**
Results are saved to JSON - reuse previous research without re-running agents

---

## Troubleshooting

### "API key not found"
```bash
# Set environment variable
export ANTHROPIC_API_KEY='your-key'

# Or pass in config
config = {'llm': {'api_key': 'your-key', ...}}
```

### "Module not found: anthropic"
```bash
pip install anthropic
# or
pip install -r requirements.txt
```

### "Rate limit exceeded"
- Wait a moment and retry
- Reduce concurrent requests
- Upgrade API tier

### Want to test without costs?
- Use Mock mode (default if no config)
- Or use Ollama locally

---

## Security Best Practices

1. **Never commit API keys to git**
   ```bash
   # Use environment variables
   export ANTHROPIC_API_KEY='...'
   ```

2. **Use .env files** (not committed)
   ```bash
   # .env
   ANTHROPIC_API_KEY=sk-ant-...
   OPENAI_API_KEY=sk-...
   ```

3. **Rotate keys** if exposed

4. **Monitor usage** via provider dashboards

---

## Next Steps

1. **Get an API key** from your preferred provider
2. **Set environment variable** or pass in config
3. **Run the example** script to see LLM agents in action
4. **Access via web dashboard** - agents show which model they're using

For web dashboard with LLM agents:
```bash
python climate_research_system/web/app.py
```

The dashboard will show:
- Which LLM model each agent uses
- Token usage per research
- LLM-generated analysis in results

**Enjoy intelligent, AI-powered climate research! 🌍**
