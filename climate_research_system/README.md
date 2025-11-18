# Climate Research Agent Orchestration System

A modular, agent-based system for collecting, validating, and presenting climate change research data for cities.

## Overview

This system uses an orchestration pattern with specialized agents to automate climate research workflows:

**Research → Local Data Collection → Presentation**

Each module uses autonomous agents coordinated by orchestrators to ensure data quality and consistency.

## Architecture

```
climate_research_system/
├── core/                    # Core framework
│   ├── agent_base.py       # Base Agent class
│   ├── message.py          # Message system for agent communication
│   └── state_manager.py    # State persistence (JSON)
├── research/               # Research Module
│   ├── orchestrator.py    # Research Orchestrator
│   ├── agents/            # Research agents
│   │   └── climate_data.py
│   └── validators/        # Validation agents (TODO)
├── data_collection/       # Local Data Collection Module (TODO)
├── presentation/          # Presentation Module (TODO)
├── utils/                 # Utilities
│   └── file_opener.py    # File operations
├── examples/              # Example scripts
│   └── research_berlin.py
└── data/                  # Persisted research results
```

## Features

### Core Framework
- **Agent Base Class**: All agents inherit from `Agent` with standardized interface
- **Message System**: Typed messages for inter-agent communication
- **State Management**: Persistent storage of research results and agent states
- **Status Tracking**: Real-time agent status monitoring
- **Error Handling**: Comprehensive error tracking and reporting

### Research Module

#### Climate Data Agent
Collects historical and projected climate data:
- Temperature trends (avg, min, max)
- Precipitation patterns
- Extreme weather events
- Climate zone classification

**Data Sources** (to be implemented):
- NOAA Climate Data Online
- World Bank Climate Portal
- OpenWeatherMap API

#### Research Orchestrator
Coordinates multiple research agents:
- Task distribution
- Result aggregation
- Cross-validation
- Report generation

### Planned Agents

**Research Module:**
- EmissionsAgent - GHG emissions, carbon footprint
- VulnerabilityAgent - Climate risks and hazards
- AdaptationAgent - Climate action plans
- ResilienceAgent - Infrastructure resilience
- GreenInfrastructureAgent - Parks, green roofs, urban forests
- EnergyAgent - Renewable energy, efficiency programs

**Validation Agents:**
- SourceCredibilityValidator
- CrossReferenceValidator
- RecencyValidator
- ConsistencyValidator

## Quick Start

### Run the Example

```bash
cd climate_research_system
python examples/research_berlin.py
```

### Basic Usage

```python
from research.orchestrator import ResearchOrchestrator
from research.agents.climate_data import ClimateDataAgent

# Initialize orchestrator
orchestrator = ResearchOrchestrator(storage_dir="data")

# Register agents
climate_agent = ClimateDataAgent(agent_id="climate_001")
orchestrator.register_agent(climate_agent)

# Conduct research
results = orchestrator.research_city(
    city="Berlin",
    country="Germany",
    years=30
)

# Access results
print(results['summary'])
print(results['validation_report'])
```

## Data Flow

1. **Task Definition**: User specifies city and research parameters
2. **Agent Dispatch**: Orchestrator sends tasks to relevant agents
3. **Data Collection**: Agents fetch data from their sources
4. **Validation**: Each agent validates its own data
5. **Aggregation**: Orchestrator combines all agent results
6. **Cross-Validation**: Orchestrator validates consistency across agents
7. **Persistence**: Results saved to JSON files
8. **Reporting**: Validation report and recommendations generated

## Agent Communication

Agents communicate via typed messages:

```python
# Request message
message = Message(
    type=MessageType.REQUEST,
    sender="orchestrator",
    recipient="climate_agent",
    payload={"city": "Berlin", "country": "Germany"}
)

# Response message
response = agent.handle_message(message)
```

## Data Validation

Multi-layer validation approach:

1. **Agent-Level**: Each agent validates its own data
   - Required fields present
   - Data ranges reasonable
   - Format correctness

2. **Orchestrator-Level**: Cross-agent validation
   - Consistency across sources
   - Completeness scoring
   - Conflict resolution

3. **Confidence Scoring**: Each data point gets a confidence score based on:
   - Number of sources
   - Source credibility
   - Data recency
   - Consistency across sources

## Current Status

✅ **Completed:**
- Core agent framework
- Message system
- State management
- ClimateDataAgent (structure)
- Research Orchestrator
- Example script

🚧 **In Progress:**
- Real API integrations
- Additional research agents
- Validation agents

📋 **Planned:**
- Local Data Collection Module
- Presentation Module
- Web scraping capabilities
- Advanced validation rules
- Dashboard/visualization

## Development

### Adding a New Agent

1. Create agent class inheriting from `Agent`
2. Implement `execute()` method for main task
3. Implement `validate()` method for data validation
4. Register with orchestrator

Example:

```python
from core.agent_base import Agent

class MyAgent(Agent):
    def execute(self, task):
        # Collect data
        return results

    def validate(self, data):
        # Validate data
        return {'valid': True, 'errors': []}
```

### API Integration

TODO: Add API keys to agent config:

```python
agent = ClimateDataAgent(
    config={
        'api_keys': {
            'noaa': 'YOUR_API_KEY',
            'worldbank': 'YOUR_KEY'
        }
    }
)
```

## Climate Focus

This system is designed for comprehensive climate change research on cities:

- **Climate Baseline**: Historical trends, current conditions
- **Emissions**: GHG inventory, sector breakdown
- **Vulnerabilities**: Flood risk, heat islands, drought
- **Adaptation**: Climate action plans, implemented measures
- **Resilience**: Infrastructure, early warning systems
- **Green Infrastructure**: Parks, urban forests, ecosystem services
- **Energy Transition**: Renewable adoption, efficiency programs

## Requirements

- Python 3.7+
- No external dependencies for core system
- API keys required for data collection (TODO)

## License

TBD

## Contributing

This is a research project. Contributions welcome!

## Next Steps

1. Implement real API integrations for ClimateDataAgent
2. Create additional research agents
3. Build validation agents
4. Implement Local Data Collection Module
5. Implement Presentation Module
6. Add web scraping capabilities
7. Create visualization tools
