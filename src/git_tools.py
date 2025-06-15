"""Git operations for MCP PR analyzer."""
import subprocess
import json
import os
from typing import Dict, List, Optional
from pathlib import Path


class GitAnalyzer:
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).resolve()
        
    def _run_git_command(self, command: List[str]) -> str:
        """Run a git command and return the output."""
        try:
            result = subprocess.run(
                ["git"] + command,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            raise Exception(f"Git command failed: {e.stderr}")
    
    def get_file_changes(self, target_branch: str = "main", max_tokens: int = 25000) -> Dict:
        """
        Analyze file changes between current branch and target branch.
        Returns structured data about changes, respecting token limits.
        """
        try:
            # Get list of changed files
            changed_files = self._run_git_command([
                "diff", "--name-status", f"{target_branch}...HEAD"
            ]).split('\n')
            
            # Get diff stats
            stats = self._run_git_command([
                "diff", "--stat", f"{target_branch}...HEAD"
            ])
            
            # Get the full diff
            full_diff = self._run_git_command([
                "diff", f"{target_branch}...HEAD"
            ])
            
            # Parse changed files
            file_changes = []
            for line in changed_files:
                if line.strip():
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        status = parts[0]
                        filename = parts[1]
                        file_changes.append({
                            "status": status,
                            "filename": filename,
                            "change_type": self._get_change_type(status)
                        })
            
            # Handle token limit
            truncated_diff = self._truncate_diff(full_diff, max_tokens - 2000)  # Reserve space for metadata
            
            return {
                "branch_comparison": f"{target_branch}...HEAD",
                "total_files_changed": len(file_changes),
                "file_changes": file_changes,
                "diff_stats": stats,
                "diff_content": truncated_diff,
                "truncated": len(full_diff) > len(truncated_diff),
                "original_diff_size": len(full_diff),
                "change_summary": self._summarize_changes(file_changes)
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "branch_comparison": f"{target_branch}...HEAD",
                "total_files_changed": 0,
                "file_changes": [],
                "diff_stats": "",
                "diff_content": "",
                "truncated": False
            }
    
    def _get_change_type(self, status: str) -> str:
        """Convert git status to human-readable change type."""
        status_map = {
            'A': 'added',
            'M': 'modified',
            'D': 'deleted',
            'R': 'renamed',
            'C': 'copied',
            'T': 'type_changed'
        }
        return status_map.get(status[0], 'unknown')
    
    def _truncate_diff(self, diff: str, max_chars: int) -> str:
        """Truncate diff to fit within token limits while preserving structure."""
        if len(diff) <= max_chars:
            return diff
        
        # Try to truncate at file boundaries
        lines = diff.split('\n')
        truncated_lines = []
        current_size = 0
        
        for line in lines:
            line_size = len(line) + 1  # +1 for newline
            if current_size + line_size > max_chars:
                truncated_lines.append(f"\n... [DIFF TRUNCATED - {len(lines) - len(truncated_lines)} more lines] ...")
                break
            truncated_lines.append(line)
            current_size += line_size
        
        return '\n'.join(truncated_lines)
    
    def _summarize_changes(self, file_changes: List[Dict]) -> Dict:
        """Create a high-level summary of changes."""
        summary = {
            "added": 0,
            "modified": 0,
            "deleted": 0,
            "renamed": 0,
            "file_types": {},
            "directories": set()
        }
        
        for change in file_changes:
            change_type = change["change_type"]
            filename = change["filename"]
            
            # Count by change type
            if change_type in summary:
                summary[change_type] += 1
            
            # Track file extensions
            if '.' in filename:
                ext = filename.split('.')[-1]
                summary["file_types"][ext] = summary["file_types"].get(ext, 0) + 1
            
            # Track directories
            directory = os.path.dirname(filename)
            if directory:
                summary["directories"].add(directory)
        
        # Convert set to list for JSON serialization
        summary["directories"] = list(summary["directories"])
        
        return summary
    
    def get_commit_messages(self, target_branch: str = "main", limit: int = 10) -> List[Dict]:
        """Get recent commit messages for context."""
        try:
            log_output = self._run_git_command([
                "log", f"{target_branch}...HEAD", 
                "--pretty=format:%H|%s|%an|%ad", 
                "--date=short",
                f"-{limit}"
            ])
            
            commits = []
            for line in log_output.split('\n'):
                if line.strip():
                    parts = line.split('|')
                    if len(parts) >= 4:
                        commits.append({
                            "hash": parts[0],
                            "message": parts[1],
                            "author": parts[2],
                            "date": parts[3]
                        })
            
            return commits
        except Exception as e:
            return [{"error": str(e)}]
    
    def get_branch_info(self) -> Dict:
        """Get current branch information."""
        try:
            current_branch = self._run_git_command(["branch", "--show-current"])
            remote_branches = self._run_git_command(["branch", "-r"]).split('\n')
            
            return {
                "current_branch": current_branch,
                "remote_branches": [b.strip() for b in remote_branches if b.strip()],
                "is_git_repo": True
            }
        except Exception as e:
            return {
                "current_branch": None,
                "remote_branches": [],
                "is_git_repo": False,
                "error": str(e)
            }