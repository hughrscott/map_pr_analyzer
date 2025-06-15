"""MCP Server for PR Analysis and Template Suggestions."""

from fastmcp import FastMCP
from typing import Dict, Optional
import json
import os
from pathlib import Path

from git_tools import GitAnalyzer
from templates import TemplateManager

# Initialize MCP server
mcp = FastMCP("PR Template Analyzer")

# Initialize components
git_analyzer = GitAnalyzer()
template_manager = TemplateManager()


@mcp.tool()
def analyze_file_changes(
    target_branch: str = "main", 
    repo_path: str = ".",
    max_tokens: int = 25000
) -> Dict:
    """
    Analyze file changes between current branch and target branch.
    
    Returns comprehensive git diff data including:
    - List of changed files with their status
    - Diff statistics
    - Actual diff content (truncated if needed)
    - Change summary and metadata
    
    Args:
        target_branch: Branch to compare against (default: main)
        repo_path: Path to git repository (default: current directory)
        max_tokens: Maximum tokens for diff content (default: 25000)
    """
    try:
        # Update git analyzer path if needed
        if repo_path != ".":
            global git_analyzer
            git_analyzer = GitAnalyzer(repo_path)
        
        # Get comprehensive change analysis
        changes = git_analyzer.get_file_changes(target_branch, max_tokens)
        
        # Add additional context
        branch_info = git_analyzer.get_branch_info()
        commit_messages = git_analyzer.get_commit_messages(target_branch, limit=5)
        
        # Combine all data
        result = {
            **changes,
            "branch_info": branch_info,
            "recent_commits": commit_messages,
            "analysis_timestamp": "2025-06-14",  # Current date
            "tool_version": "1.0.0"
        }
        
        return result
        
    except Exception as e:
        return {
            "error": f"Failed to analyze file changes: {str(e)}",
            "target_branch": target_branch,
            "repo_path": repo_path,
            "total_files_changed": 0,
            "file_changes": [],
            "diff_stats": "",
            "diff_content": "",
            "truncated": False
        }


@mcp.tool()
def get_pr_templates() -> Dict:
    """
    Get all available PR templates with their content and metadata.
    
    Returns:
        Dictionary containing all PR templates with:
        - Template content
        - Metadata (name, description, suitable_for)
        - File paths
        - Usage guidelines
    """
    try:
        templates = template_manager.get_all_templates()
        
        # Add summary information
        template_names = list(templates.keys())
        
        result = {
            "templates": templates,
            "available_templates": template_names,
            "total_templates": len(templates),
            "template_directory": str(template_manager.templates_dir),
            "usage_note": "Each template includes metadata about when it's most suitable to use."
        }
        
        return result
        
    except Exception as e:
        return {
            "error": f"Failed to load PR templates: {str(e)}",
            "templates": {},
            "available_templates": [],
            "total_templates": 0
        }


@mcp.tool()
def suggest_template(
    change_analysis: Optional[Dict] = None,
    target_branch: str = "main",
    repo_path: str = "."
) -> Dict:
    """
    Suggest appropriate PR templates based on code changes.
    
    This tool provides both automated suggestions and raw data for Claude
    to make intelligent template recommendations.
    
    Args:
        change_analysis: Pre-analyzed change data (if None, will analyze automatically)
        target_branch: Branch to compare against
        repo_path: Path to git repository
    """
    try:
        # Get change analysis if not provided
        if change_analysis is None:
            change_analysis = analyze_file_changes(target_branch, repo_path)
        
        # Get available templates
        templates_data = get_pr_templates()
        
        # Get basic suggestions (Claude will do better analysis)
        suggestions = template_manager.get_template_suggestions(change_analysis)
        
        # Prepare comprehensive data for Claude's analysis
        result = {
            "suggested_templates": suggestions,
            "change_analysis": change_analysis,
            "available_templates": templates_data["templates"],
            "analysis_metadata": {
                "files_changed": change_analysis.get("total_files_changed", 0),
                "change_types": change_analysis.get("change_summary", {}),
                "branch_comparison": change_analysis.get("branch_comparison", ""),
                "has_diff_content": bool(change_analysis.get("diff_content", "")),
                "diff_truncated": change_analysis.get("truncated", False)
            },
            "recommendation_note": (
                "The 'suggested_templates' field contains basic heuristic suggestions. "
                "Use the 'change_analysis' and 'available_templates' data to make "
                "more intelligent recommendations based on the actual code changes."
            )
        }
        
        return result
        
    except Exception as e:
        return {
            "error": f"Failed to suggest templates: {str(e)}",
            "suggested_templates": {
                "primary_suggestions": ["feature"],
                "secondary_suggestions": [],
                "confidence": "none"
            },
            "change_analysis": {},
            "available_templates": {}
        }


# Additional utility tools

@mcp.tool()
def get_git_status() -> Dict:
    """Get current git repository status and branch information."""
    try:
        branch_info = git_analyzer.get_branch_info()
        return {
            "status": "success",
            **branch_info
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "is_git_repo": False
        }


@mcp.tool()
def validate_pr_description(
    description: str,
    template_name: str,
    change_analysis: Optional[Dict] = None
) -> Dict:
    """
    Validate a PR description against a template and change analysis.
    
    Args:
        description: The PR description to validate
        template_name: Name of the template to validate against
        change_analysis: Analysis of the actual changes
    """
    try:
        # Get the template
        template = template_manager.get_template(template_name)
        if not template:
            return {
                "valid": False,
                "error": f"Template '{template_name}' not found",
                "available_templates": template_manager.list_available_templates()
            }
        
        # Basic validation (Claude will do more sophisticated analysis)
        validation_result = {
            "template_used": template_name,
            "description_length": len(description),
            "template_content": template.get("content", ""),
            "change_analysis": change_analysis or {},
            "basic_checks": {
                "has_description": len(description.strip()) > 0,
                "reasonable_length": 10 < len(description) < 5000,
                "contains_checklist": "- [ ]" in description or "- [x]" in description
            },
            "validation_note": (
                "This provides basic validation data. Use Claude's analysis "
                "to determine if the description adequately covers the changes "
                "and follows the template structure."
            )
        }
        
        return validation_result
        
    except Exception as e:
        return {
            "valid": False,
            "error": f"Validation failed: {str(e)}",
            "template_used": template_name
        }


if __name__ == "__main__":
    print("Starting MCP PR Template Analyzer Server...")
    print("Available tools:")
    print("- analyze_file_changes: Get git diff data and file changes")
    print("- get_pr_templates: Load available PR templates")  
    print("- suggest_template: Get template suggestions based on changes")
    print("- get_git_status: Check git repository status")
    print("- validate_pr_description: Validate PR description against template")
    print("\nServer running...")
    
    mcp.run()