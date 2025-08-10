#!/usr/bin/env python3
"""
Advanced Code Review Engine for Claude Code Automation
Comprehensive code analysis with multiple specialized agents.
"""

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import ast
import importlib.util

class CodeReviewEngine:
    def __init__(self, project_dir: str = None):
        self.project_dir = Path(project_dir or ".")
        self.claude_dir = self.project_dir / ".claude"
        self.agents_dir = self.claude_dir / "agents"
        
        # Review results storage
        self.security_issues = []
        self.performance_issues = []
        self.coverage_issues = []
        self.auto_fixes = []
        
        # Quality metrics
        self.quality_score = 10.0
        self.blocker_issues = 0
        
    def run_comprehensive_review(self) -> Dict[str, Any]:
        """Run complete code review with all specialized agents."""
        print("[Review] Starting Comprehensive Code Review...")
        
        # Get changed files
        changed_files = self.get_changed_files()
        if not changed_files:
            print("[Info] No files to review")
            return {"status": "no_changes"}
        
        print(f"[Files] Reviewing {len(changed_files)} files: {', '.join(changed_files[:5])}{'...' if len(changed_files) > 5 else ''}")
        
        # Run specialized analyses
        self.run_security_analysis(changed_files)
        self.run_performance_analysis(changed_files) 
        self.run_coverage_analysis(changed_files)
        self.run_code_quality_analysis(changed_files)
        
        # Generate comprehensive report
        report = self.generate_review_report()
        
        # Apply auto-fixes if enabled
        if self.should_auto_fix():
            self.apply_auto_fixes()
        
        # Determine if merge should be blocked
        block_merge = self.should_block_merge()
        
        return {
            "status": "completed",
            "quality_score": self.quality_score,
            "blocker_issues": self.blocker_issues,
            "block_merge": block_merge,
            "report": report,
            "auto_fixes_applied": len(self.auto_fixes)
        }
    
    def run_security_analysis(self, files: List[str]):
        """Analyze code for security vulnerabilities."""
        print("[Security] Running Security Analysis...")
        
        config = self.load_agent_config("security-scanner")
        if not config:
            return
            
        patterns = config.get("security_patterns", {})
        
        for file_path in files:
            if not file_path.endswith(('.py', '.js', '.ts', '.jsx', '.tsx')):
                continue
                
            content = self.read_file_safe(file_path)
            if not content:
                continue
                
            # Check for secrets
            secrets_found = self.scan_for_secrets(content, patterns.get("secrets", {}))
            self.security_issues.extend(secrets_found)
            
            # Check for injection vulnerabilities  
            injections_found = self.scan_for_injections(content, patterns.get("injections", {}))
            self.security_issues.extend(injections_found)
            
            # Check for crypto issues
            crypto_issues = self.scan_for_crypto_issues(content, patterns.get("crypto_issues", {}))
            self.security_issues.extend(crypto_issues)
        
        critical_issues = [issue for issue in self.security_issues if issue["severity"] == "critical"]
        if critical_issues:
            self.blocker_issues += len(critical_issues)
            self.quality_score -= len(critical_issues) * 2.0
            
        print(f"[Security] {len(self.security_issues)} issues found ({len(critical_issues)} critical)")
    
    def scan_for_secrets(self, content: str, patterns: Dict) -> List[Dict]:
        """Scan for hardcoded secrets."""
        issues = []
        
        for category, pattern_list in patterns.items():
            for pattern in pattern_list:
                matches = re.finditer(pattern, content, re.MULTILINE)
                for match in matches:
                    issues.append({
                        "type": "secret",
                        "category": category,
                        "severity": "critical",
                        "message": f"Hardcoded {category} detected",
                        "line": content[:match.start()].count('\n') + 1,
                        "fix_suggestion": "Move to environment variables"
                    })
        
        return issues
    
    def scan_for_injections(self, content: str, patterns: Dict) -> List[Dict]:
        """Scan for injection vulnerabilities."""
        issues = []
        
        for category, pattern_list in patterns.items():
            for pattern in pattern_list:
                matches = re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE)
                for match in matches:
                    issues.append({
                        "type": "injection",
                        "category": category,
                        "severity": "critical",
                        "message": f"Potential {category} vulnerability",
                        "line": content[:match.start()].count('\n') + 1,
                        "fix_suggestion": "Use parameterized queries/sanitized inputs"
                    })
        
        return issues
    
    def scan_for_crypto_issues(self, content: str, patterns: Dict) -> List[Dict]:
        """Scan for cryptographic issues."""
        issues = []
        
        for category, pattern_list in patterns.items():
            for pattern in pattern_list:
                matches = re.finditer(pattern, content, re.MULTILINE | re.IGNORECASE)
                for match in matches:
                    issues.append({
                        "type": "crypto",
                        "category": category,
                        "severity": "high",
                        "message": f"Weak cryptographic practice: {category}",
                        "line": content[:match.start()].count('\n') + 1,
                        "fix_suggestion": "Use strong cryptographic algorithms"
                    })
        
        return issues
    
    def run_performance_analysis(self, files: List[str]):
        """Analyze code for performance issues."""
        print("[Performance] Running Performance Analysis...")
        
        config = self.load_agent_config("performance-analyzer")
        if not config:
            return
            
        patterns = config.get("performance_patterns", {})
        
        for file_path in files:
            if not file_path.endswith('.py'):  # Focus on Python for now
                continue
                
            content = self.read_file_safe(file_path)
            if not content:
                continue
                
            # Analyze complexity
            complexity_issues = self.analyze_complexity(file_path, content, config.get("complexity_thresholds", {}))
            self.performance_issues.extend(complexity_issues)
            
            # Check for inefficient patterns
            inefficiency_issues = self.scan_performance_patterns(content, patterns)
            self.performance_issues.extend(inefficiency_issues)
        
        high_issues = [issue for issue in self.performance_issues if issue["severity"] in ["critical", "high"]]
        if high_issues:
            self.quality_score -= len(high_issues) * 0.5
            
        print(f"[Performance] {len(self.performance_issues)} issues found ({len(high_issues)} high-priority)")
    
    def analyze_complexity(self, file_path: str, content: str, thresholds: Dict) -> List[Dict]:
        """Analyze code complexity metrics."""
        issues = []
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Count complexity (simplified cyclomatic complexity)
                    complexity = self.calculate_cyclomatic_complexity(node)
                    length = len(content.split('\n')[node.lineno-1:node.end_lineno])
                    params = len(node.args.args)
                    
                    if complexity > thresholds.get("cyclomatic_complexity", {}).get("error", 20):
                        issues.append({
                            "type": "complexity",
                            "severity": "high",
                            "message": f"Function '{node.name}' has high complexity: {complexity}",
                            "line": node.lineno,
                            "fix_suggestion": "Consider breaking into smaller functions"
                        })
                    
                    if length > thresholds.get("function_length", {}).get("error", 100):
                        issues.append({
                            "type": "length",
                            "severity": "medium",
                            "message": f"Function '{node.name}' is too long: {length} lines",
                            "line": node.lineno,
                            "fix_suggestion": "Split into smaller, focused functions"
                        })
                    
                    if params > thresholds.get("parameter_count", {}).get("error", 8):
                        issues.append({
                            "type": "parameters",
                            "severity": "medium", 
                            "message": f"Function '{node.name}' has too many parameters: {params}",
                            "line": node.lineno,
                            "fix_suggestion": "Consider using a configuration object"
                        })
        
        except SyntaxError:
            pass  # Skip files with syntax errors
        
        return issues
    
    def calculate_cyclomatic_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate simplified cyclomatic complexity."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.Try):
                complexity += len(child.handlers)
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def scan_performance_patterns(self, content: str, patterns: Dict) -> List[Dict]:
        """Scan for performance anti-patterns."""
        issues = []
        
        for category, pattern_list in patterns.items():
            for pattern_info in pattern_list:
                pattern = pattern_info.get("pattern", "")
                matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
                
                for match in matches:
                    issues.append({
                        "type": "performance",
                        "category": category,
                        "severity": "medium",
                        "message": pattern_info.get("issue", "Performance issue detected"),
                        "line": content[:match.start()].count('\n') + 1,
                        "fix_suggestion": pattern_info.get("suggestion", "Consider optimization")
                    })
        
        return issues
    
    def run_coverage_analysis(self, files: List[str]):
        """Analyze test coverage."""
        print("[Coverage] Running Test Coverage Analysis...")
        
        try:
            # Run coverage analysis
            result = subprocess.run(
                ["coverage", "run", "-m", "pytest", "--tb=no", "-q"],
                cwd=self.project_dir,
                capture_output=True,
                text=True
            )
            
            # Get coverage report
            coverage_result = subprocess.run(
                ["coverage", "report", "--format=json"],
                cwd=self.project_dir,
                capture_output=True,
                text=True
            )
            
            if coverage_result.returncode == 0:
                coverage_data = json.loads(coverage_result.stdout)
                total_coverage = coverage_data.get("totals", {}).get("percent_covered", 0)
                
                if total_coverage < 70:
                    self.blocker_issues += 1
                    self.coverage_issues.append({
                        "type": "coverage",
                        "severity": "critical",
                        "message": f"Test coverage too low: {total_coverage:.1f}%",
                        "fix_suggestion": "Add more comprehensive tests"
                    })
                elif total_coverage < 85:
                    self.coverage_issues.append({
                        "type": "coverage", 
                        "severity": "medium",
                        "message": f"Test coverage below target: {total_coverage:.1f}%",
                        "fix_suggestion": "Increase test coverage"
                    })
                
                print(f"[Coverage] {total_coverage:.1f}% ({len(self.coverage_issues)} issues)")
            
        except (subprocess.SubprocessError, FileNotFoundError, json.JSONDecodeError):
            print("[Warning] Coverage analysis skipped (coverage.py not available)")
    
    def run_code_quality_analysis(self, files: List[str]):
        """Run general code quality analysis."""
        print("[Quality] Running Code Quality Analysis...")
        
        for file_path in files:
            content = self.read_file_safe(file_path)
            if not content:
                continue
                
            # Basic quality checks
            lines = content.split('\n')
            
            # Check for long lines
            for i, line in enumerate(lines, 1):
                if len(line) > 120:
                    self.quality_score -= 0.1
            
            # Check for TODO/FIXME comments
            todo_count = content.count('TODO') + content.count('FIXME') + content.count('HACK')
            if todo_count > 5:
                self.quality_score -= 0.2
    
    def should_auto_fix(self) -> bool:
        """Determine if auto-fixes should be applied."""
        return True  # For now, always attempt auto-fixes
    
    def apply_auto_fixes(self):
        """Apply automatic fixes to code."""
        print("[AutoFix] Applying Auto-fixes...")
        
        # Format code
        try:
            subprocess.run(["black", "."], cwd=self.project_dir, check=True)
            self.auto_fixes.append("Applied Black code formatting")
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        
        try:
            subprocess.run(["isort", "."], cwd=self.project_dir, check=True) 
            self.auto_fixes.append("Sorted imports with isort")
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        
        print(f"[AutoFix] Applied {len(self.auto_fixes)} auto-fixes")
    
    def should_block_merge(self) -> bool:
        """Determine if merge should be blocked."""
        return self.blocker_issues > 0 or self.quality_score < 7.0
    
    def generate_review_report(self) -> str:
        """Generate comprehensive review report."""
        report = f"""# Code Review Report
        
**Generated**: {datetime.now().isoformat()}
**Quality Score**: {self.quality_score:.1f}/10.0
**Blocker Issues**: {self.blocker_issues}

## Security Analysis
{len(self.security_issues)} issues found

"""
        
        if self.security_issues:
            report += "### Critical Security Issues:\n"
            for issue in self.security_issues[:5]:  # Top 5
                report += f"- **{issue['type'].title()}**: {issue['message']} (Line {issue.get('line', 'N/A')})\n"
                report += f"  *Fix*: {issue.get('fix_suggestion', 'Manual review required')}\n"
        
        report += f"""
## Performance Analysis
{len(self.performance_issues)} issues found

"""
        
        if self.performance_issues:
            report += "### Performance Issues:\n"
            for issue in self.performance_issues[:5]:
                report += f"- **{issue['type'].title()}**: {issue['message']} (Line {issue.get('line', 'N/A')})\n"
                report += f"  *Fix*: {issue.get('fix_suggestion', 'Consider optimization')}\n"
        
        report += f"""
## Test Coverage
{len(self.coverage_issues)} issues found

"""
        
        if self.coverage_issues:
            for issue in self.coverage_issues:
                report += f"- **{issue['type'].title()}**: {issue['message']}\n"
                report += f"  *Fix*: {issue.get('fix_suggestion', 'Add more tests')}\n"
        
        if self.auto_fixes:
            report += "\n## Auto-fixes Applied\n"
            for fix in self.auto_fixes:
                report += f"- [OK] {fix}\n"
        
        report += f"""
## Summary

- **Total Issues**: {len(self.security_issues) + len(self.performance_issues) + len(self.coverage_issues)}
- **Auto-fixes Applied**: {len(self.auto_fixes)}
- **Merge Recommendation**: {"BLOCK" if self.should_block_merge() else "APPROVE"}

"""
        
        return report
    
    def get_changed_files(self) -> List[str]:
        """Get list of changed files from git."""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD~1..HEAD"],
                cwd=self.project_dir,
                capture_output=True,
                text=True
            )
            return result.stdout.strip().split('\n') if result.stdout.strip() else []
        except subprocess.SubprocessError:
            return []
    
    def read_file_safe(self, file_path: str) -> str:
        """Safely read file content."""
        try:
            with open(self.project_dir / file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except (FileNotFoundError, UnicodeDecodeError):
            return ""
    
    def load_agent_config(self, agent_name: str) -> Optional[Dict]:
        """Load agent configuration."""
        config_path = self.agents_dir / f"{agent_name}.json"
        if not config_path.exists():
            return None
            
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return None

def main():
    """Main entry point for code review engine."""
    if len(sys.argv) > 1:
        project_dir = sys.argv[1]
    else:
        project_dir = "."
    
    engine = CodeReviewEngine(project_dir)
    result = engine.run_comprehensive_review()
    
    if result.get("status") == "no_changes":
        print("[Info] No changes to review")
        return
    
    print("\n" + "="*60)
    print(result["report"])
    
    if result["block_merge"]:
        print("[BLOCKED] MERGE BLOCKED - Critical issues found")
        sys.exit(1)
    else:
        print("[APPROVED] Code review passed - Merge approved")
        sys.exit(0)

if __name__ == "__main__":
    main()