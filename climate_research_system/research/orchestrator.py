"""
Research Orchestrator - Coordinates all research agents.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import sys
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

sys.path.append(str(Path(__file__).parent.parent))
from core.agent_base import Agent, AgentStatus
from core.message import Message, MessageType
from core.state_manager import StateManager
import logging


class ResearchOrchestrator:
    """
    Orchestrates research agents to collect and validate climate data.

    Responsibilities:
    - Manage multiple research agents
    - Coordinate data collection workflow
    - Aggregate results from multiple agents
    - Validate cross-agent data consistency
    - Generate comprehensive research reports
    """

    def __init__(self, storage_dir: str = "data"):
        """
        Initialize Research Orchestrator.

        Args:
            storage_dir: Directory for data storage
        """
        self.agents: Dict[str, Agent] = {}
        self.state_manager = StateManager(storage_dir)
        self.research_history = []
        self.logger = self._setup_logger()
        self.created_at = datetime.now()

    def _setup_logger(self) -> logging.Logger:
        """Setup orchestrator logger."""
        logger = logging.getLogger("orchestrator.research")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - ResearchOrchestrator - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def register_agent(self, agent: Agent) -> None:
        """
        Register an agent with the orchestrator.

        Args:
            agent: Agent instance to register
        """
        self.agents[agent.agent_id] = agent
        self.logger.info(f"Registered agent: {agent.name} ({agent.agent_id})")

    def unregister_agent(self, agent_id: str) -> bool:
        """
        Remove an agent from the orchestrator.

        Args:
            agent_id: ID of agent to remove

        Returns:
            True if agent was removed
        """
        if agent_id in self.agents:
            del self.agents[agent_id]
            self.logger.info(f"Unregistered agent: {agent_id}")
            return True
        return False

    def research_city(self, city: str, country: str, **kwargs) -> Dict[str, Any]:
        """
        Conduct comprehensive research on a city.

        Args:
            city: City name
            country: Country name
            **kwargs: Additional parameters for agents

        Returns:
            Comprehensive research results
        """
        research_id = f"{city.lower().replace(' ', '_')}_{country.lower()}"
        self.logger.info(f"Starting research for: {city}, {country}")

        research_task = {
            'city': city,
            'country': country,
            'research_id': research_id,
            'started_at': datetime.now().isoformat(),
            **kwargs
        }

        # Separate agents by type: data collection, validation, presentation
        validation_agent = None
        presentation_agent = None
        data_agents = {}

        for agent_id, agent in self.agents.items():
            if 'validation' in agent_id.lower() or agent.name == "ValidationAgent":
                validation_agent = agent
            elif 'presentation' in agent_id.lower() or agent.name == "Presentation Agent":
                presentation_agent = agent
            else:
                data_agents[agent_id] = agent

        # Execute data collection agents first
        agent_results = {}
        for agent_id, agent in data_agents.items():
            self.logger.info(f"Executing agent: {agent.name}")
            try:
                message = Message(
                    type=MessageType.REQUEST,
                    sender="orchestrator",
                    recipient=agent_id,
                    payload=research_task
                )
                response = agent.handle_message(message)

                if response and response.type == MessageType.RESPONSE:
                    agent_results[agent_id] = response.payload
                    self.logger.info(f"✓ {agent.name} completed successfully")
                elif response and response.type == MessageType.ERROR:
                    self.logger.error(f"✗ {agent.name} error: {response.payload}")
                    agent_results[agent_id] = {'error': response.payload}
                else:
                    self.logger.warning(f"? {agent.name} no response")

            except Exception as e:
                self.logger.error(f"✗ {agent.name} exception: {str(e)}")
                agent_results[agent_id] = {'error': str(e)}

        # Execute validation agent with all agent results
        validation_report = {}
        if validation_agent:
            self.logger.info(f"Executing validation: {validation_agent.name}")
            try:
                validation_task = {
                    'city': city,
                    'country': country,
                    'agent_results': agent_results,
                    **kwargs
                }
                message = Message(
                    type=MessageType.REQUEST,
                    sender="orchestrator",
                    recipient=validation_agent.agent_id,
                    payload=validation_task
                )
                response = validation_agent.handle_message(message)

                if response and response.type == MessageType.RESPONSE:
                    validation_report = response.payload
                    self.logger.info(f"✓ Validation completed")
                else:
                    self.logger.warning("Validation agent produced no response")
                    validation_report = self._cross_validate_results({'agent_results': agent_results})

            except Exception as e:
                self.logger.error(f"✗ Validation error: {str(e)}")
                validation_report = self._cross_validate_results({'agent_results': agent_results})
        else:
            # Fallback to basic validation if no ValidationAgent
            self.logger.info("No ValidationAgent registered, using basic validation")
            validation_report = self._cross_validate_results({'agent_results': agent_results})

        # Execute presentation agent AFTER validation (final step)
        presentation = {}
        if presentation_agent:
            self.logger.info(f"Generating presentation: {presentation_agent.name}")
            try:
                presentation_task = {
                    'city': city,
                    'country': country,
                    'agent_results': agent_results,
                    'validation_report': validation_report,
                    **kwargs
                }
                message = Message(
                    type=MessageType.REQUEST,
                    sender="orchestrator",
                    recipient=presentation_agent.agent_id,
                    payload=presentation_task
                )
                response = presentation_agent.handle_message(message)

                if response and response.type == MessageType.RESPONSE:
                    presentation = response.payload
                    self.logger.info(f"✓ Presentation generated")
                else:
                    self.logger.warning("Presentation agent produced no response")

            except Exception as e:
                self.logger.error(f"✗ Presentation error: {str(e)}")
        else:
            self.logger.info("No Presentation Agent registered, skipping presentation generation")

        # Aggregate results
        results = self._aggregate_results(city, country, research_id, agent_results)
        results['validation_report'] = validation_report
        results['presentation'] = presentation

        # Add source tracking from validation
        if 'sources' in validation_report:
            results['sources'] = validation_report['sources']
            results['total_sources'] = validation_report.get('total_sources', 0)

        if 'provenance_report' in validation_report:
            results['provenance'] = validation_report['provenance_report']

        # Save results
        self.state_manager.save_research_results(research_id, results)
        self.state_manager.save_validation_report(research_id, validation_report)
        if presentation:
            self.state_manager.save_presentation(research_id, presentation)

        # Update history
        self.research_history.append({
            'research_id': research_id,
            'city': city,
            'country': country,
            'completed_at': datetime.now().isoformat(),
            'agents_used': list(self.agents.keys()),
            'status': 'completed',
            'has_presentation': bool(presentation)
        })

        self.logger.info(f"Research completed for {city}, {country}")
        return results

    def research_city_parallel(
        self,
        city: str,
        country: str,
        max_workers: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Conduct comprehensive research on a city with PARALLEL execution.

        Data collection agents run in parallel for faster results.
        ValidationAgent still runs sequentially after all agents complete.

        Args:
            city: City name
            country: Country name
            max_workers: Maximum parallel workers (default: number of agents)
            **kwargs: Additional parameters for agents

        Returns:
            Comprehensive research results (same format as research_city)
        """
        research_id = f"{city.lower().replace(' ', '_')}_{country.lower()}"
        self.logger.info(f"Starting PARALLEL research for: {city}, {country}")

        research_task = {
            'city': city,
            'country': country,
            'research_id': research_id,
            'started_at': datetime.now().isoformat(),
            **kwargs
        }

        # Separate agents by type: data collection, validation, presentation
        validation_agent = None
        presentation_agent = None
        data_agents = {}

        for agent_id, agent in self.agents.items():
            if 'validation' in agent_id.lower() or agent.name == "ValidationAgent":
                validation_agent = agent
            elif 'presentation' in agent_id.lower() or agent.name == "Presentation Agent":
                presentation_agent = agent
            else:
                data_agents[agent_id] = agent

        # Execute data collection agents IN PARALLEL
        start_time = time.time()
        agent_results = self._execute_agents_parallel(
            agents=data_agents,
            research_task=research_task,
            max_workers=max_workers
        )
        execution_time = time.time() - start_time

        self.logger.info(f"Parallel execution completed in {execution_time:.2f} seconds")

        # Execute validation agent with all agent results (sequential)
        validation_report = {}
        if validation_agent:
            self.logger.info(f"Executing validation: {validation_agent.name}")
            try:
                validation_task = {
                    'city': city,
                    'country': country,
                    'agent_results': agent_results,
                    **kwargs
                }
                message = Message(
                    type=MessageType.REQUEST,
                    sender="orchestrator",
                    recipient=validation_agent.agent_id,
                    payload=validation_task
                )
                response = validation_agent.handle_message(message)

                if response and response.type == MessageType.RESPONSE:
                    validation_report = response.payload
                    self.logger.info(f"✓ Validation completed")
                else:
                    self.logger.warning("Validation agent produced no response")
                    validation_report = self._cross_validate_results({'agent_results': agent_results})

            except Exception as e:
                self.logger.error(f"✗ Validation error: {str(e)}")
                validation_report = self._cross_validate_results({'agent_results': agent_results})
        else:
            # Fallback to basic validation if no ValidationAgent
            self.logger.info("No ValidationAgent registered, using basic validation")
            validation_report = self._cross_validate_results({'agent_results': agent_results})

        # Execute presentation agent AFTER validation (final step)
        presentation = {}
        if presentation_agent:
            self.logger.info(f"Generating presentation: {presentation_agent.name}")
            try:
                presentation_task = {
                    'city': city,
                    'country': country,
                    'agent_results': agent_results,
                    'validation_report': validation_report,
                    **kwargs
                }
                message = Message(
                    type=MessageType.REQUEST,
                    sender="orchestrator",
                    recipient=presentation_agent.agent_id,
                    payload=presentation_task
                )
                response = presentation_agent.handle_message(message)

                if response and response.type == MessageType.RESPONSE:
                    presentation = response.payload
                    self.logger.info(f"✓ Presentation generated")
                else:
                    self.logger.warning("Presentation agent produced no response")

            except Exception as e:
                self.logger.error(f"✗ Presentation error: {str(e)}")
        else:
            self.logger.info("No Presentation Agent registered, skipping presentation generation")

        # Aggregate results
        results = self._aggregate_results(city, country, research_id, agent_results)
        results['validation_report'] = validation_report
        results['presentation'] = presentation

        # Add execution time metadata
        results['metadata']['execution_time_seconds'] = round(execution_time, 2)
        results['metadata']['execution_mode'] = 'parallel'

        # Add source tracking from validation
        if 'sources' in validation_report:
            results['sources'] = validation_report['sources']
            results['total_sources'] = validation_report.get('total_sources', 0)

        if 'provenance_report' in validation_report:
            results['provenance'] = validation_report['provenance_report']

        # Save results
        self.state_manager.save_research_results(research_id, results)
        self.state_manager.save_validation_report(research_id, validation_report)
        if presentation:
            self.state_manager.save_presentation(research_id, presentation)

        # Update history
        self.research_history.append({
            'research_id': research_id,
            'city': city,
            'country': country,
            'completed_at': datetime.now().isoformat(),
            'agents_used': list(self.agents.keys()),
            'status': 'completed',
            'execution_time': execution_time,
            'execution_mode': 'parallel',
            'has_presentation': bool(presentation)
        })

        self.logger.info(f"Parallel research completed for {city}, {country} in {execution_time:.2f}s")
        return results

    def _execute_agents_parallel(
        self,
        agents: Dict[str, Agent],
        research_task: Dict[str, Any],
        max_workers: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute multiple agents in parallel using ThreadPoolExecutor.

        Args:
            agents: Dictionary of agents to execute
            research_task: Task payload for agents
            max_workers: Maximum parallel workers

        Returns:
            Dictionary of agent results
        """
        agent_results = {}

        if not agents:
            return agent_results

        # Default to number of agents if not specified
        if max_workers is None:
            max_workers = len(agents)

        self.logger.info(f"Executing {len(agents)} agents in parallel (max_workers={max_workers})")

        # Create executor
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all agents
            future_to_agent = {}

            for agent_id, agent in agents.items():
                future = executor.submit(
                    self._execute_single_agent,
                    agent_id,
                    agent,
                    research_task
                )
                future_to_agent[future] = (agent_id, agent)

            # Collect results as they complete
            for future in as_completed(future_to_agent):
                agent_id, agent = future_to_agent[future]

                try:
                    result = future.result(timeout=300)  # 5 minute timeout per agent
                    agent_results[agent_id] = result

                except Exception as e:
                    self.logger.error(f"✗ {agent.name} parallel execution error: {str(e)}")
                    agent_results[agent_id] = {'error': str(e)}

        return agent_results

    def _execute_single_agent(
        self,
        agent_id: str,
        agent: Agent,
        research_task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a single agent (helper for parallel execution).

        Args:
            agent_id: Agent identifier
            agent: Agent instance
            research_task: Task payload

        Returns:
            Agent result
        """
        self.logger.info(f"⚡ Executing agent in parallel: {agent.name}")

        try:
            message = Message(
                type=MessageType.REQUEST,
                sender="orchestrator",
                recipient=agent_id,
                payload=research_task
            )
            response = agent.handle_message(message)

            if response and response.type == MessageType.RESPONSE:
                self.logger.info(f"✓ {agent.name} completed successfully")
                return response.payload
            elif response and response.type == MessageType.ERROR:
                self.logger.error(f"✗ {agent.name} error: {response.payload}")
                return {'error': response.payload}
            else:
                self.logger.warning(f"? {agent.name} no response")
                return {'error': 'No response from agent'}

        except Exception as e:
            self.logger.error(f"✗ {agent.name} exception: {str(e)}")
            return {'error': str(e)}

    def _aggregate_results(
        self,
        city: str,
        country: str,
        research_id: str,
        agent_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Aggregate results from all agents.

        Args:
            city: City name
            country: Country name
            research_id: Research identifier
            agent_results: Results from each agent

        Returns:
            Aggregated results dictionary
        """
        return {
            'research_id': research_id,
            'city': city,
            'country': country,
            'completed_at': datetime.now().isoformat(),
            'agent_results': agent_results,
            'summary': self._generate_summary(agent_results),
            'metadata': {
                'agents_used': list(self.agents.keys()),
                'total_agents': len(self.agents),
                'successful_agents': sum(
                    1 for r in agent_results.values()
                    if 'error' not in r
                )
            }
        }

    def _generate_summary(self, agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate summary of research findings.

        Args:
            agent_results: Results from all agents

        Returns:
            Summary dictionary
        """
        summary = {
            'data_completeness': 0.0,
            'errors': [],
            'warnings': [],
            'key_findings': []
        }

        total_completeness = 0
        valid_agents = 0

        for agent_id, result in agent_results.items():
            if 'error' in result:
                summary['errors'].append(f"{agent_id}: {result['error']}")
                continue

            # Extract completeness if available
            if isinstance(result, dict):
                valid_agents += 1
                # Try to find completeness in nested validation results
                if 'metrics' in result:
                    # This could be improved to extract actual completeness scores
                    total_completeness += 0.5  # Placeholder

        if valid_agents > 0:
            summary['data_completeness'] = total_completeness / valid_agents

        return summary

    def _cross_validate_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate consistency across agent results.

        Args:
            results: Aggregated results

        Returns:
            Validation report
        """
        report = {
            'validated_at': datetime.now().isoformat(),
            'overall_valid': True,
            'inconsistencies': [],
            'missing_data': [],
            'recommendations': []
        }

        agent_results = results.get('agent_results', {})

        # Check for missing data from agents
        for agent_id, agent in self.agents.items():
            if agent_id not in agent_results:
                report['missing_data'].append(f"No data from {agent.name}")
                report['overall_valid'] = False
            elif 'error' in agent_results[agent_id]:
                report['missing_data'].append(
                    f"{agent.name} failed: {agent_results[agent_id]['error']}"
                )
                report['overall_valid'] = False

        # Add recommendations
        if report['missing_data']:
            report['recommendations'].append(
                "Re-run research with additional data sources"
            )

        if results.get('summary', {}).get('data_completeness', 0) < 0.7:
            report['recommendations'].append(
                "Data completeness below 70% - consider additional data collection"
            )

        return report

    def get_research_status(self, research_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a research task.

        Args:
            research_id: Research identifier

        Returns:
            Status dictionary or None
        """
        return self.state_manager.load_research_results(research_id)

    def list_research(self) -> List[str]:
        """
        List all completed research.

        Returns:
            List of research IDs
        """
        return self.state_manager.list_research_results()

    def get_agent_status(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a specific agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Agent state dictionary
        """
        if agent_id in self.agents:
            return self.agents[agent_id].get_state()
        return None

    def reset_all_agents(self) -> None:
        """Reset all registered agents to initial state."""
        for agent in self.agents.values():
            agent.reset()
        self.logger.info("All agents reset")

    def __repr__(self) -> str:
        return f"ResearchOrchestrator(agents={len(self.agents)})"
