"""
Skills module for agent system.

This module provides the framework for loading, managing, and executing skills.
Skills are markdown files with frontmatter that provide specialized instructions
for specific tasks.
"""

from extern_agent.agent.skills.types import (
    Skill,
    SkillEntry,
    SkillMetadata,
    SkillInstallSpec,
    LoadSkillsResult,
)
from extern_agent.agent.skills.loader import SkillLoader
from extern_agent.agent.skills.manager import SkillManager
from extern_agent.agent.skills.service import SkillService
from extern_agent.agent.skills.formatter import format_skills_for_prompt

__all__ = [
    "Skill",
    "SkillEntry",
    "SkillMetadata",
    "SkillInstallSpec",
    "LoadSkillsResult",
    "SkillLoader",
    "SkillManager",
    "SkillService",
    "format_skills_for_prompt",
]
