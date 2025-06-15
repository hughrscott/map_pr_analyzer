"""PR template management for MCP server."""

import os
from pathlib import Path
from typing import Dict, List, Optional


class TemplateManager:
    def __init__(self, templates_dir: str = "templates"):
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(exist_ok=True)
    
    def get_all_templates(self) -> Dict[str, Dict]:
        """Get all available PR templates with metadata."""
        templates = {}
        
        # Define template metadata
        template_metadata = {
            "feature": {
                "name": "Feature",
                "description": "For new features and enhancements",
                "suitable_for": [
                    "New functionality",
                    "Feature enhancements",
                    "New API endpoints",
                    "UI/UX improvements"
                ]
            },
            "bugfix": {
                "name": "Bug Fix",
                "description": "For fixing bugs and issues",
                "suitable_for": [
                    "Bug fixes",
                    "Error handling improvements",
                    "Performance fixes",
                    "Security fixes"
                ]
            },
            "hotfix": {
                "name": "Hotfix",
                "description": "For critical production issues",
                "suitable_for": [
                    "Critical production bugs",
                    "Security vulnerabilities",
                    "Service outages",
                    "Data corruption fixes"
                ]
            },
            "docs": {
                "name": "Documentation",
                "description": "For documentation changes",
                "suitable_for": [
                    "README updates",
                    "API documentation",
                    "Code comments",
                    "Architecture docs"
                ]
            }
        }
        
        # Load template files
        for template_file in self.templates_dir.glob("*.md"):
            template_name = template_file.stem
            
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                templates[template_name] = {
                    "content": content,
                    "file_path": str(template_file),
                    "metadata": template_metadata.get(template_name, {
                        "name": template_name.title(),
                        "description": f"Template for {template_name}",
                        "suitable_for": []
                    })
                }
            except Exception as e:
                templates[template_name] = {
                    "error": f"Could not load template: {str(e)}",
                    "file_path": str(template_file)
                }
        
        return templates
    
    def get_template(self, template_name: str) -> Optional[Dict]:
        """Get a specific template by name."""
        templates = self.get_all_templates()
        return templates.get(template_name)
    
    def get_template_suggestions(self, change_analysis: Dict) -> Dict:
        """
        Provide template suggestions based on change analysis.
        This is a simple heuristic - Claude will do the real analysis.
        """
        suggestions = {
            "primary_suggestions": [],
            "secondary_suggestions": [],
            "analysis_data": change_analysis
        }
        
        # Simple heuristic rules (Claude will do better analysis)
        file_changes = change_analysis.get("file_changes", [])
        change_summary = change_analysis.get("change_summary", {})
        
        # Count different types of files
        doc_files = 0
        code_files = 0
        config_files = 0
        test_files = 0
        
        for change in file_changes:
            filename = change.get("filename", "").lower()
            
            if any(doc_ext in filename for doc_ext in ['.md', '.txt', '.rst', 'readme', 'docs/']):
                doc_files += 1
            elif any(test_ext in filename for test_ext in ['test_', '_test', 'spec_', '_spec', 'tests/']):
                test_files += 1
            elif any(config_ext in filename for config_ext in ['.json', '.yaml', '.yml', '.toml', '.ini', 'config']):
                config_files += 1
            else:
                code_files += 1
        
        # Simple suggestion logic
        total_files = len(file_changes)
        
        if total_files == 0:
            suggestions["primary_suggestions"] = ["feature"]  # Default
        elif doc_files > code_files:
            suggestions["primary_suggestions"] = ["docs"]
            suggestions["secondary_suggestions"] = ["feature"]
        elif any(word in str(change_analysis).lower() for word in ["fix", "bug", "error", "issue"]):
            suggestions["primary_suggestions"] = ["bugfix"]
            suggestions["secondary_suggestions"] = ["feature"]
        elif any(word in str(change_analysis).lower() for word in ["critical", "urgent", "hotfix", "production"]):
            suggestions["primary_suggestions"] = ["hotfix"]
            suggestions["secondary_suggestions"] = ["bugfix"]
        else:
            suggestions["primary_suggestions"] = ["feature"]
            suggestions["secondary_suggestions"] = ["docs", "bugfix"]
        
        # Add confidence scores (Claude will do this better)
        suggestions["confidence"] = "low"  # Since this is just heuristics
        suggestions["reasoning"] = "Basic heuristic analysis - Claude will provide better suggestions"
        
        return suggestions
    
    def create_custom_template(self, name: str, content: str) -> bool:
        """Create a new custom template."""
        try:
            template_path = self.templates_dir / f"{name}.md"
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error creating template {name}: {e}")
            return False
    
    def list_available_templates(self) -> List[str]:
        """Get a simple list of available template names."""
        return list(self.get_all_templates().keys())