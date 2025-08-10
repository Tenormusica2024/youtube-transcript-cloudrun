#!/usr/bin/env python3
"""
Claude Code Automation System
Manages automated sub-agent execution based on git hooks and file changes.
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class ClaudeAutomationSystem:
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir or os.getcwd())
        self.claude_dir = self.base_dir / ".claude"
        self.hooks_config = self.claude_dir / "hooks.json"
        self.agents_dir = self.claude_dir / "agents"

    def load_hooks_config(self) -> Dict:
        """Load hooks configuration from JSON file."""
        if not self.hooks_config.exists():
            return {"hooks": {}, "global_settings": {}}

        with open(self.hooks_config, "r") as f:
            return json.load(f)

    def load_agent_config(self, agent_type: str) -> Optional[Dict]:
        """Load agent configuration."""
        agent_file = self.agents_dir / f"{agent_type}.json"
        if not agent_file.exists():
            print(f"Warning: Agent config not found: {agent_file}")
            return None

        with open(agent_file, "r") as f:
            return json.load(f)

    def execute_hook(self, hook_name: str, context: Dict = None):
        """Execute a specific hook with given context."""
        config = self.load_hooks_config()

        if hook_name not in config.get("hooks", {}):
            print(f"Hook '{hook_name}' not found in configuration")
            return

        hook_config = config["hooks"][hook_name]
        agents = hook_config.get("agents", [])

        print(f"[Claude] Executing hook: {hook_name}")
        print(f"[Info] Description: {hook_config.get('description', 'No description')}")

        for agent_config in agents:
            self.execute_agent(agent_config, context or {})

    def execute_agent(self, agent_config: Dict, context: Dict):
        """Execute a specific agent with given configuration."""
        agent_type = agent_config.get("type")
        task = agent_config.get("task", "General task")
        conditions = agent_config.get("conditions", {})
        actions = agent_config.get("actions", [])

        # Check conditions
        if not self.check_conditions(conditions, context):
            print(f"[Skip] Skipping agent {agent_type}: conditions not met")
            return

        print(f"[Agent] Executing agent: {agent_type}")
        print(f"[Task] Task: {task}")

        # Load agent-specific config
        agent_details = self.load_agent_config(agent_type)
        if not agent_details:
            return

        # Execute Claude Code with specialized agent
        self.call_claude_agent(agent_type, task, actions, agent_details)

    def check_conditions(self, conditions: Dict, context: Dict) -> bool:
        """Check if conditions are met for agent execution."""
        # Check file changes
        if "files_changed" in conditions:
            changed_files = context.get("changed_files", [])
            patterns = conditions["files_changed"]

            if not any(self.match_pattern(f, patterns) for f in changed_files):
                return False

        # Check minimum changes
        if "min_changes" in conditions:
            changes_count = len(context.get("changed_files", []))
            if changes_count < conditions["min_changes"]:
                return False

        # Check branch
        if "branch" in conditions:
            current_branch = self.get_current_branch()
            branch_condition = conditions["branch"]

            if branch_condition.startswith("!"):
                if current_branch == branch_condition[1:]:
                    return False
            else:
                if current_branch != branch_condition:
                    return False

        return True

    def match_pattern(self, filename: str, patterns: List[str]) -> bool:
        """Check if filename matches any of the given patterns."""
        import fnmatch

        return any(fnmatch.fnmatch(filename, pattern) for pattern in patterns)

    def get_current_branch(self) -> str:
        """Get current git branch."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True,
                text=True,
                cwd=self.base_dir,
            )
            return result.stdout.strip()
        except:
            return "unknown"

    def get_changed_files(self) -> List[str]:
        """Get list of changed files from git."""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD~1..HEAD"],
                capture_output=True,
                text=True,
                cwd=self.base_dir,
            )
            return result.stdout.strip().split("\n") if result.stdout.strip() else []
        except:
            return []

    def call_claude_agent(
        self, agent_type: str, task: str, actions: List[str], agent_details: Dict
    ):
        """Call Claude Code with specialized agent."""
        # Construct the prompt for Claude
        prompt = f"""
🤖 **Automated {agent_type.title()} Task**

**Task**: {task}

**Actions to perform**:
{chr(10).join(f'- {action}' for action in actions)}

**Agent Configuration**:
- Capabilities: {', '.join(agent_details.get('agent_config', {}).get('capabilities', []))}
- Working Directory: {self.base_dir}

**Context**:
- Current Branch: {self.get_current_branch()}
- Changed Files: {', '.join(self.get_changed_files())}
- Timestamp: {datetime.now().isoformat()}

Please execute this automated task according to the agent specifications.
"""

        # Execute claude command
        try:
            claude_cmd = ["claude", "--prompt", prompt]
            print(f"[Execute] Calling Claude Code...")

            result = subprocess.run(
                claude_cmd, cwd=self.base_dir, capture_output=True, text=True
            )

            if result.returncode == 0:
                print("[OK] Agent execution completed successfully")
                if result.stdout:
                    print(
                        "[Output]",
                        (
                            result.stdout[:200] + "..."
                            if len(result.stdout) > 200
                            else result.stdout
                        ),
                    )
            else:
                print("[ERROR] Agent execution failed")
                if result.stderr:
                    print("[Error]", result.stderr)

        except Exception as e:
            print(f"[ERROR] Failed to execute Claude agent: {e}")


def main():
    """Main entry point for automation system."""
    if len(sys.argv) < 2:
        print("Usage: python automation-system.py <hook_name>")
        print("Available hooks: post-commit, pre-push, file-added, weekly-sync")
        return

    hook_name = sys.argv[1]
    automation = ClaudeAutomationSystem()

    # Gather context
    context = {
        "changed_files": automation.get_changed_files(),
        "current_branch": automation.get_current_branch(),
        "timestamp": datetime.now().isoformat(),
    }

    automation.execute_hook(hook_name, context)


if __name__ == "__main__":
    main()
