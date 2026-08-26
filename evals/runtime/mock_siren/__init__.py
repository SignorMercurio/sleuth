"""Mock SIREN server for SLEUTH runtime regression tests.

Public entry points:
    load_scenario / load_all_scenarios / validate_scenario  -- scenario files
    MockSirenSession                                        -- direct Python API
    mock_siren.server                                       -- MCP stdio server
"""

from .api import MockSirenSession, RunResult
from .faults import FaultEngine
from .policy import blacklist_match
from .scenario import (
    load_all_scenarios,
    load_scenario,
    scenario_paths,
    validate_scenario,
)
from .shell import CommandResult, HostSimulator

__all__ = [
    "CommandResult",
    "FaultEngine",
    "HostSimulator",
    "MockSirenSession",
    "RunResult",
    "blacklist_match",
    "load_all_scenarios",
    "load_scenario",
    "scenario_paths",
    "validate_scenario",
]
