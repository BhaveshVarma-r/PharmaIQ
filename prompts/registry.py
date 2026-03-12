import json
import os
import re
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

PROMPTS_ROOT = Path(__file__).parent / "versions"

ACTIVE_VERSIONS = {
    "soma": "v1_1",
    "soma_critique": "v1_0",
    "pulse": "v1_0",
    "pulse_critique": "v1_0",
    "planner": "v1_0",
    "planner_critique": "v1_0",
}


class PromptNotFoundError(Exception):
    pass


class PromptVersionError(Exception):
    pass


class PromptRegistry:
    def __init__(self, active_versions=None):
        self.active_versions = active_versions or ACTIVE_VERSIONS.copy()
        self._cache = {}
        self._metadata_cache = {}

    def get_prompt(self, agent, prompt_name, variables=None, version=None):
        resolved_version = version or self.active_versions.get(agent)
        if not resolved_version:
            raise PromptVersionError(
                "No active version configured for agent: {}".format(agent)
            )
        cache_key = "{}/{}/{}".format(agent, resolved_version, prompt_name)
        if cache_key not in self._cache:
            prompt_path = (
                PROMPTS_ROOT / agent / resolved_version / "{}.txt".format(prompt_name)
            )
            if not prompt_path.exists():
                raise PromptNotFoundError(
                    "Prompt not found: {}".format(prompt_path)
                )
            self._cache[cache_key] = prompt_path.read_text(encoding="utf-8")
        raw_prompt = self._cache[cache_key]
        if variables:
            return self._inject_variables(raw_prompt, variables)
        return raw_prompt

    def get_metadata(self, agent, version=None):
        resolved_version = version or self.active_versions.get(agent)
        cache_key = "{}/{}/metadata".format(agent, resolved_version)
        if cache_key not in self._metadata_cache:
            metadata_path = (
                PROMPTS_ROOT / agent / resolved_version / "metadata.json"
            )
            if not metadata_path.exists():
                raise PromptNotFoundError(
                    "Metadata not found: {}".format(metadata_path)
                )
            with open(metadata_path, encoding="utf-8") as f:
                self._metadata_cache[cache_key] = json.load(f)
        return self._metadata_cache[cache_key]

    def list_versions(self, agent):
        agent_path = PROMPTS_ROOT / agent
        if not agent_path.exists():
            return []
        return sorted([d.name for d in agent_path.iterdir() if d.is_dir()])

    def list_agents(self):
        if not PROMPTS_ROOT.exists():
            return []
        return sorted([d.name for d in PROMPTS_ROOT.iterdir() if d.is_dir()])

    def get_active_version(self, agent):
        return self.active_versions.get(agent, "unknown")

    def set_active_version(self, agent, version):
        available = self.list_versions(agent)
        if version not in available:
            raise PromptVersionError(
                "Version {} not available for agent {}. Available: {}".format(
                    version, agent, available
                )
            )
        self.active_versions[agent] = version
        keys_to_clear = [k for k in self._cache if k.startswith("{}/".format(agent))]
        for key in keys_to_clear:
            del self._cache[key]
        logger.info("Prompt version changed for {}: {}".format(agent, version))

    def get_all_active_metadata(self):
        result = {}
        for agent in self.list_agents():
            try:
                result[agent] = self.get_metadata(agent)
            except PromptNotFoundError:
                result[agent] = {"error": "metadata.json not found"}
        return result

    def _inject_variables(self, template, variables):
        result = template
        for key, value in variables.items():
            placeholder = "{" + key + "}"
            if placeholder in result:
                result = result.replace(placeholder, str(value))
        remaining = re.findall(r'\{[a-zA-Z_][a-zA-Z0-9_]*\}', result)
        if remaining:
            logger.warning(
                "Unfilled prompt variables: {}. Provided: {}".format(
                    remaining, list(variables.keys())
                )
            )
        return result

    def validate_all_prompts(self):
        report = {"status": "ok", "agents": {}, "errors": []}
        for agent in self.list_agents():
            agent_report = {
                "version": self.get_active_version(agent),
                "prompts": {}
            }
            try:
                metadata = self.get_metadata(agent)
                for prompt_key, prompt_file in metadata.get("prompts", {}).items():
                    prompt_name = prompt_file.replace(".txt", "")
                    try:
                        self.get_prompt(agent, prompt_name)
                        agent_report["prompts"][prompt_name] = "ok"
                    except Exception as e:
                        agent_report["prompts"][prompt_name] = "ERROR: {}".format(e)
                        report["errors"].append(
                            "{}/{}: {}".format(agent, prompt_name, e)
                        )
                        report["status"] = "errors_found"
            except Exception as e:
                agent_report["metadata"] = "ERROR: {}".format(e)
                report["errors"].append("{}/metadata: {}".format(agent, e))
                report["status"] = "errors_found"
            report["agents"][agent] = agent_report
        return report


registry = PromptRegistry()