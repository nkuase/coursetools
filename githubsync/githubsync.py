#!/usr/bin/env python3
"""
Enhanced Git Repository Manager
A PyQt6 application for syncing multiple git repositories with smart error detection and auto-fix

This application demonstrates:
- Reading configuration files
- GUI programming with PyQt6
- Process execution and management
- Smart error analysis and auto-fix
- Health checking and diagnostics
- Portable configuration with environment variables
- Automatic add/commit before push
- Safe pull with uncommitted changes detection
"""

import sys
import os
import json
import subprocess
from pathlib import Path
from typing import List, Dict
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
    QWidget, QPushButton, QTextEdit, QLabel, QProgressBar,
    QMessageBox, QFileDialog, QGroupBox, QScrollArea,
    QFrame, QSplitter
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont


class GitDiagnostics:
    """
    Git repository diagnostics and auto-fix utilities
    Educational tool for common git issues
    """
    
    @staticmethod
    def analyze_error(error_message: str, repo_path: Path) -> Dict:
        """Analyze git error and suggest fixes"""
        error_info = {
            'type': 'unknown',
            'description': 'Unknown git error',
            'fix_available': False,
            'fix_description': '',
            'commands': []
        }
        
        error_lower = error_message.lower()
        
        # Non-fast-forward push error (local behind remote)
        if "non-fast-forward" in error_lower or "tip of your current branch is behind" in error_lower:
            error_info = {
                'type': 'non_fast_forward',
                'description': 'Local branch is behind remote - need to pull first',
                'fix_available': True,
                'fix_description': 'Pull remote changes, then push again',
                'commands': [
                    'git pull --rebase',
                    'git push'
                ]
            }
        
        # Branch mismatch (master -> main)
        elif "no such ref was fetched" in error_lower and "master" in error_lower:
            error_info = {
                'type': 'branch_mismatch',
                'description': 'Local branch tracking old branch name (master vs main)',
                'fix_available': True,
                'fix_description': 'Switch to main branch and update tracking',
                'commands': [
                    'git fetch origin',
                    'git checkout -b main origin/main || git checkout main',
                    'git branch --set-upstream-to=origin/main main'
                ]
            }
        
        # Diverged branches
        elif "have diverged" in error_lower:
            error_info = {
                'type': 'diverged_branches',
                'description': 'Local and remote branches have diverged',
                'fix_available': True,
                'fix_description': 'Fetch and merge remote changes',
                'commands': [
                    'git fetch origin',
                    'git pull --rebase'
                ]
            }
        
        # Authentication issues
        elif any(auth_term in error_lower for auth_term in ['authentication', 'permission denied', 'fatal: could not read']):
            error_info = {
                'type': 'auth_error',
                'description': 'Authentication or permission error',
                'fix_available': False,
                'fix_description': 'Check your SSH keys or access tokens',
                'commands': []
            }
        
        # Uncommitted changes
        elif "uncommitted changes" in error_lower or "working tree clean" in error_lower:
            error_info = {
                'type': 'uncommitted_changes',
                'description': 'Repository has uncommitted changes',
                'fix_available': True,
                'fix_description': 'Stash changes, pull, then restore',
                'commands': [
                    'git stash push -m "Auto-stash before pull"',
                    'git pull',
                    'git stash pop'
                ]
            }
        
        # Network/connectivity issues
        elif any(net_term in error_lower for net_term in ['network', 'timeout', 'connection', 'could not resolve']):
            error_info = {
                'type': 'network_error',
                'description': 'Network connectivity issue',
                'fix_available': False,
                'fix_description': 'Check internet connection and repository URL',
                'commands': []
            }
        
        return error_info
    
    @staticmethod
    def check_repository_health(repo_path: Path) -> Dict:
        """Perform pre-flight checks on repository"""
        health_info = {
            'healthy': True,
            'issues': [],
            'warnings': []
        }
        
        try:
            # Check if it's actually a git repository
            git_dir = repo_path / '.git'
            if not git_dir.exists():
                health_info['healthy'] = False
                health_info['issues'].append('Not a git repository')
                return health_info
            
            # Check current branch
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                current_branch = result.stdout.strip()
                if not current_branch:
                    health_info['warnings'].append('Repository is in detached HEAD state')
            
            # Check for uncommitted changes
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout.strip():
                health_info['warnings'].append('Repository has uncommitted changes')
            
            # Check remote tracking
            result = subprocess.run(
                ['git', 'remote', '-v'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0 or not result.stdout.strip():
                health_info['issues'].append('No remote repository configured')
                health_info['healthy'] = False
            
        except Exception as e:
            health_info['healthy'] = False
            health_info['issues'].append(f'Health check failed: {str(e)}')
        
        return health_info
    
    @staticmethod
    def check_uncommitted_changes(repo_path: Path) -> Dict:
        """Check for uncommitted changes in repository"""
        status_info = {
            'has_changes': False,
            'files': [],
            'staged': [],
            'untracked': [],
            'modified': []
        }
        
        try:
            result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout.strip():
                status_info['has_changes'] = True
                lines = result.stdout.strip().split('\n')
                
                for line in lines:
                    if len(line) >= 3:
                        staged_status = line[0]    # First character: staged status
                        unstaged_status = line[1]  # Second character: unstaged status
                        filename = line[3:]
                        
                        # Check for untracked files
                        if staged_status == '?' and unstaged_status == '?':
                            status_info['untracked'].append(filename)
                            status_info['files'].append(filename)
                        else:
                            # Check staged changes
                            if staged_status not in [' ', '?']:
                                status_info['staged'].append(filename)
                            
                            # Check unstaged changes
                            if unstaged_status not in [' ', '?']:
                                status_info['modified'].append(filename)
                            
                            # Add to general files list
                            if filename not in status_info['files']:
                                status_info['files'].append(filename)
            
        except Exception as e:
            # If we can't check, assume there might be changes for safety
            status_info['has_changes'] = True
            status_info['files'] = [f'Error checking status: {str(e)}']
        
        return status_info
    
    @staticmethod
    def auto_fix_repository(repo_path: Path, error_type: str, commands: List[str]) -> Dict:
        """Attempt to automatically fix common repository issues"""
        fix_result = {
            'success': False,
            'message': '',
            'output': []
        }
        
        try:
            # Special handling for non-fast-forward errors
            if error_type == 'non_fast_forward':
                # First, let's check the current status
                fix_result['output'].append("=== Checking repository status ===")
                
                status_result = subprocess.run(
                    ['git', 'status', '--porcelain'],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if status_result.stdout.strip():
                    fix_result['output'].append(f"Found uncommitted changes: {status_result.stdout.strip()}")
                    # If there are uncommitted changes, stash them first
                    fix_result['output'].append("$ git stash push -m 'Auto-stash before pull-rebase'")
                    stash_result = subprocess.run(
                        ['git', 'stash', 'push', '-m', 'Auto-stash before pull-rebase'],
                        cwd=repo_path,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    if stash_result.stdout.strip():
                        fix_result['output'].append(stash_result.stdout.strip())
                else:
                    fix_result['output'].append("Working directory is clean")
                
                # Now execute the pull --rebase
                fix_result['output'].append("$ git pull --rebase")
                pull_result = subprocess.run(
                    ['git', 'pull', '--rebase'],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=60  # Give more time for rebase
                )
                
                if pull_result.stdout.strip():
                    fix_result['output'].append(pull_result.stdout.strip())
                if pull_result.stderr.strip():
                    fix_result['output'].append(f"Pull stderr: {pull_result.stderr.strip()}")
                
                if pull_result.returncode != 0:
                    fix_result['message'] = f"Auto-fix failed during git pull --rebase"
                    return fix_result
                
                # If we stashed changes, restore them
                if status_result.stdout.strip():
                    fix_result['output'].append("$ git stash pop")
                    pop_result = subprocess.run(
                        ['git', 'stash', 'pop'],
                        cwd=repo_path,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    if pop_result.stdout.strip():
                        fix_result['output'].append(pop_result.stdout.strip())
                    if pop_result.returncode != 0:
                        fix_result['output'].append("Warning: Could not restore stashed changes automatically")
                
                # Now try to push
                fix_result['output'].append("$ git push")
                push_result = subprocess.run(
                    ['git', 'push'],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if push_result.stdout.strip():
                    fix_result['output'].append(push_result.stdout.strip())
                if push_result.stderr.strip():
                    fix_result['output'].append(f"Push stderr: {push_result.stderr.strip()}")
                
                if push_result.returncode == 0:
                    fix_result['success'] = True
                    fix_result['message'] = "Successfully resolved non-fast-forward error and pushed changes"
                else:
                    fix_result['message'] = f"Pull --rebase succeeded but push still failed"
                
                return fix_result
            
            # Default handling for other error types
            for cmd in commands:
                cmd_parts = cmd.split()
                result = subprocess.run(
                    cmd_parts,
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                fix_result['output'].append(f"$ {cmd}")
                if result.stdout.strip():
                    fix_result['output'].append(result.stdout.strip())
                if result.stderr.strip():
                    fix_result['output'].append(f"Error: {result.stderr.strip()}")
                
                if result.returncode != 0:
                    fix_result['message'] = f"Auto-fix failed at command: {cmd}"
                    return fix_result
            
            fix_result['success'] = True
            fix_result['message'] = f"Auto-fix completed successfully for {error_type}"
            
        except Exception as e:
            fix_result['message'] = f"Auto-fix error: {str(e)}"
        
        return fix_result


class GitWorker(QThread):
    """
    Worker thread for executing git operations
    Prevents GUI freezing during long operations
    """
    progress = pyqtSignal(str)                    # Signal for progress updates
    success_output = pyqtSignal(str)              # Signal for successful operations
    error_output = pyqtSignal(str, dict)          # Signal for error messages with fix info
    finished = pyqtSignal()                       # Signal when all operations complete

    def __init__(self, repositories: List[Path], operation: str):
        super().__init__()
        self.repositories = repositories
        self.operation = operation  # 'pull' or 'push'
    
    def execute_git_command(self, cmd: List[str], repo_path: Path, timeout: int = 30) -> subprocess.CompletedProcess:
        """Execute a git command and return the result"""
        return subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=timeout
        )
    
    def perform_push_operation(self, repo_path: Path, repo_display: str) -> str:
        """Perform push operation with automatic add and commit"""
        operations = []
        
        try:
            # Check for uncommitted changes
            operations.append(f"🔍 Checking status of {repo_display}...")
            status_info = GitDiagnostics.check_uncommitted_changes(repo_path)
            
            # Debug: Show what we found
            if status_info['has_changes']:
                operations.append(f"📝 Found changes in {repo_display}:")
                if status_info['untracked']:
                    operations.append(f"  • Untracked: {', '.join(status_info['untracked'][:3])}{'...' if len(status_info['untracked']) > 3 else ''}")
                if status_info['modified']:
                    operations.append(f"  • Modified: {', '.join(status_info['modified'][:3])}{'...' if len(status_info['modified']) > 3 else ''}")
                if status_info['staged']:
                    operations.append(f"  • Staged: {', '.join(status_info['staged'][:3])}{'...' if len(status_info['staged']) > 3 else ''}")
                
                # Add all changes
                operations.append("  → Running: git add .")
                result = self.execute_git_command(['git', 'add', '.'], repo_path)
                if result.returncode != 0:
                    error_msg = f"✗ {repo_display}: git add failed"
                    if result.stderr.strip():
                        error_msg += f"\n  Error: {result.stderr.strip()}"
                    if result.stdout.strip():
                        error_msg += f"\n  Output: {result.stdout.strip()}"
                    error_msg += "\n" + "\n".join(operations)
                    return error_msg
                operations.append("  ✓ Successfully added all changes")
                
                # Commit changes
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                commit_msg = f"Auto-commit before push - {timestamp}"
                operations.append(f"  → Running: git commit -m '{commit_msg}'")
                
                result = self.execute_git_command(['git', 'commit', '-m', commit_msg], repo_path)
                
                # Debug: Show commit result
                operations.append(f"  → Commit return code: {result.returncode}")
                if result.stdout.strip():
                    operations.append(f"  → Commit stdout: {result.stdout.strip()}")
                if result.stderr.strip():
                    operations.append(f"  → Commit stderr: {result.stderr.strip()}")
                
                if result.returncode != 0:
                    # Check if it's because there's nothing to commit
                    output_text = (result.stdout + " " + result.stderr).lower()
                    if "nothing to commit" in output_text or "nothing added to commit" in output_text:
                        operations.append("  ℹ Nothing new to commit (working tree clean)")
                    else:
                        error_msg = f"✗ {repo_display}: git commit failed"
                        if result.stderr.strip():
                            error_msg += f"\n  Error: {result.stderr.strip()}"
                        if result.stdout.strip():
                            error_msg += f"\n  Output: {result.stdout.strip()}"
                        error_msg += "\n" + "\n".join(operations)
                        return error_msg
                else:
                    operations.append("  ✓ Successfully committed changes")
            else:
                operations.append(f"ℹ No uncommitted changes found in {repo_display}")
            
            # Push changes
            operations.append("  → Running: git push")
            result = self.execute_git_command(['git', 'push'], repo_path)
            
            # Debug: Show push result
            operations.append(f"  → Push return code: {result.returncode}")
            if result.stdout.strip():
                operations.append(f"  → Push stdout: {result.stdout.strip()}")
            if result.stderr.strip():
                operations.append(f"  → Push stderr: {result.stderr.strip()}")
            
            if result.returncode == 0:
                operations.append("  ✓ Successfully pushed to remote")
                success_msg = f"✓ {repo_display}: push completed successfully"
                
                # Show meaningful push output
                if result.stdout.strip():
                    output = result.stdout.strip()
                    if not any(phrase in output.lower() for phrase in ['up-to-date', 'up to date']):
                        operations.append(f"  📤 Push details: {output}")
                
                return success_msg + "\n" + "\n".join(operations)
            else:
                error_msg = f"✗ {repo_display}: git push failed"
                if result.stderr.strip():
                    error_msg += f"\n  Error: {result.stderr.strip()}"
                if result.stdout.strip():
                    error_msg += f"\n  Output: {result.stdout.strip()}"
                error_msg += "\n" + "\n".join(operations)
                return error_msg
                
        except Exception as e:
            error_msg = f"✗ {repo_display}: Push operation failed - {str(e)}"
            if operations:
                error_msg += "\n" + "\n".join(operations)
            return error_msg
    
    def perform_pull_operation(self, repo_path: Path, repo_display: str) -> str:
        """Perform pull operation with uncommitted changes check"""
        try:
            # Check for uncommitted changes first
            status_info = GitDiagnostics.check_uncommitted_changes(repo_path)
            
            if status_info['has_changes']:
                # Skip pull and report uncommitted changes
                files_list = status_info['files'][:5]  # Show first 5 files
                files_display = ", ".join(files_list)
                if len(status_info['files']) > 5:
                    files_display += f" (and {len(status_info['files']) - 5} more)"
                
                skip_msg = f"⚠ {repo_display}: SKIPPED pull - uncommitted changes detected"
                skip_msg += f"\n  Uncommitted files: {files_display}"
                skip_msg += f"\n  → Commit or stash changes before pulling"
                return skip_msg
            
            # Proceed with pull since working directory is clean
            result = self.execute_git_command(['git', 'pull'], repo_path)
            
            if result.returncode == 0:
                success_msg = f"✓ {repo_display}: pull successful"
                if result.stdout.strip():
                    output = result.stdout.strip()
                    if not any(phrase in output.lower() for phrase in ['already up to date', 'up-to-date']):
                        success_msg += f"\n  Output: {output}"
                    else:
                        success_msg += "\n  Repository already up to date"
                return success_msg
            else:
                error_msg = f"✗ {repo_display}: pull failed"
                if result.stderr.strip():
                    error_msg += f"\n  Error: {result.stderr.strip()}"
                return error_msg
                
        except Exception as e:
            return f"✗ {repo_display}: Pull operation failed - {str(e)}"
    
    def run(self):
        """Execute git operations on all repositories"""
        total_repos = len(self.repositories)
        
        for i, repo_path in enumerate(self.repositories, 1):
            try:
                # Show progress with repository path relative info
                progress_msg = f"[{i}/{total_repos}] Processing: {repo_path.name}"
                # If repo is deeply nested, show parent context
                if len(repo_path.parts) > 2:
                    parent_context = "/".join(repo_path.parts[-2:])
                    progress_msg = f"[{i}/{total_repos}] Processing: {parent_context}"
                
                self.progress.emit(progress_msg)
                
                # Format repository name for results (show relative path if nested)
                repo_display = str(repo_path.name)
                if len(repo_path.parts) > 2:
                    repo_display = "/".join(repo_path.parts[-2:])
                
                # Perform health check before operation
                health_info = GitDiagnostics.check_repository_health(repo_path)
                
                if not health_info['healthy']:
                    error_msg = f"✗ {repo_display}: Repository health check failed"
                    error_msg += f"\n  Issues: {', '.join(health_info['issues'])}"
                    
                    error_info = {
                        'repo_path': repo_path,
                        'repo_display': repo_display,
                        'analysis': {
                            'type': 'health_check_failed',
                            'description': f'Repository health issues: {", ".join(health_info["issues"])}',
                            'fix_available': False,
                            'fix_description': 'Fix repository issues manually',
                            'commands': []
                        },
                        'health': health_info
                    }
                    self.error_output.emit(error_msg, error_info)
                    continue
                
                # Execute operation based on type
                if self.operation == 'pull':
                    result_msg = self.perform_pull_operation(repo_path, repo_display)
                elif self.operation == 'push':
                    result_msg = self.perform_push_operation(repo_path, repo_display)
                else:
                    raise ValueError(f"Unknown operation: {self.operation}")
                
                # Determine if it's success, warning, or error
                if result_msg.startswith('✓'):
                    # Add health warnings if any
                    if health_info['warnings']:
                        result_msg += f"\n  ⚠ Warnings: {', '.join(health_info['warnings'])}"
                    self.success_output.emit(result_msg)
                elif result_msg.startswith('⚠'):
                    # This is a warning (like skipped pull), treat as success but with warning
                    self.success_output.emit(result_msg)
                else:
                    # This is an error, analyze it
                    error_text = result_msg
                    error_analysis = GitDiagnostics.analyze_error(error_text, repo_path)
                    
                    error_info = {
                        'repo_path': repo_path,
                        'repo_display': repo_display,
                        'analysis': error_analysis,
                        'health': health_info
                    }
                    
                    self.error_output.emit(error_text, error_info)
                        
            except subprocess.TimeoutExpired:
                repo_display = str(repo_path.name)
                if len(repo_path.parts) > 2:
                    repo_display = "/".join(repo_path.parts[-2:])
                
                error_info = {
                    'repo_path': repo_path,
                    'repo_display': repo_display,
                    'analysis': {
                        'type': 'timeout',
                        'description': 'Operation timed out after 30 seconds',
                        'fix_available': False,
                        'fix_description': 'Try again or check repository status manually',
                        'commands': []
                    },
                    'health': {}
                }
                self.error_output.emit(f"✗ {repo_display}: Operation timed out", error_info)
                
            except Exception as e:
                repo_display = str(repo_path.name)
                if len(repo_path.parts) > 2:
                    repo_display = "/".join(repo_path.parts[-2:])
                
                error_info = {
                    'repo_path': repo_path,
                    'repo_display': repo_display,
                    'analysis': {
                        'type': 'exception',
                        'description': f'Unexpected error: {str(e)}',
                        'fix_available': False,
                        'fix_description': 'Check repository manually',
                        'commands': []
                    },
                    'health': {}
                }
                self.error_output.emit(f"✗ {repo_display}: {str(e)}", error_info)
        
        # Emit completion signal
        self.finished.emit()


class ErrorFixWidget(QWidget):
    """
    Widget for displaying error analysis and auto-fix options
    """
    
    retry_requested = pyqtSignal(str)  # Signal for retry request
    
    def __init__(self, error_info: Dict, parent=None):
        super().__init__(parent)
        self.error_info = error_info
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Repository name
        repo_label = QLabel(f"Repository: {self.error_info['repo_display']}")
        repo_label.setStyleSheet("font-weight: bold; color: #8B0000;")
        layout.addWidget(repo_label)
        
        # Error analysis
        analysis = self.error_info['analysis']
        if analysis['type'] != 'unknown':
            # Error type and description
            type_label = QLabel(f"Issue: {analysis['description']}")
            type_label.setWordWrap(True)
            layout.addWidget(type_label)
            
            # Fix information
            if analysis['fix_available']:
                fix_label = QLabel(f"💡 Suggested Fix: {analysis['fix_description']}")
                fix_label.setStyleSheet("color: #2E8B57; font-style: italic;")
                fix_label.setWordWrap(True)
                layout.addWidget(fix_label)
                
                # Auto-fix buttons
                button_layout = QHBoxLayout()
                
                auto_fix_btn = QPushButton("🔧 Auto-Fix")
                auto_fix_btn.setStyleSheet("background-color: #32CD32; color: white; font-weight: bold;")
                auto_fix_btn.clicked.connect(self.perform_auto_fix)
                button_layout.addWidget(auto_fix_btn)
                
                # Special handling for non-fast-forward errors
                if analysis['type'] == 'non_fast_forward':
                    force_fix_btn = QPushButton("⚡ Force Fix")
                    force_fix_btn.setStyleSheet("background-color: #FF6347; color: white; font-weight: bold;")
                    force_fix_btn.clicked.connect(self.perform_force_fix)
                    button_layout.addWidget(force_fix_btn)
                
                manual_btn = QPushButton("📋 Show Commands")
                manual_btn.setStyleSheet("background-color: #4682B4; color: white;")
                manual_btn.clicked.connect(self.show_manual_commands)
                button_layout.addWidget(manual_btn)
                
                # Add retry button
                retry_btn = QPushButton("🔄 Retry Operation")
                retry_btn.setStyleSheet("background-color: #FF8C00; color: white; font-weight: bold;")
                retry_btn.clicked.connect(self.retry_operation)
                button_layout.addWidget(retry_btn)
                
                button_layout.addStretch()
                layout.addLayout(button_layout)
            else:
                no_fix_label = QLabel("⚠️ Manual intervention required")
                no_fix_label.setStyleSheet("color: #FF6347; font-weight: bold;")
                layout.addWidget(no_fix_label)
                
                # Still add retry button for manual fixes
                button_layout = QHBoxLayout()
                retry_btn = QPushButton("🔄 Retry After Manual Fix")
                retry_btn.setStyleSheet("background-color: #FF8C00; color: white; font-weight: bold;")
                retry_btn.clicked.connect(self.retry_operation)
                button_layout.addWidget(retry_btn)
                button_layout.addStretch()
                layout.addLayout(button_layout)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("color: #D3D3D3;")
        layout.addWidget(separator)
    
    def retry_operation(self):
        """Request retry of the operation for this repository"""
        repo_path = str(self.error_info['repo_path'])
        self.retry_requested.emit(repo_path)
    
    def perform_force_fix(self):
        """Perform aggressive fix for non-fast-forward errors"""
        analysis = self.error_info['analysis']
        repo_path = self.error_info['repo_path']
        
        # Show warning dialog
        reply = QMessageBox.warning(
            self, 
            "Force Fix Warning",
            f"This will perform an aggressive fix for the non-fast-forward error:\n\n"
            f"1. Fetch latest changes from remote\n"
            f"2. Reset local branch to match remote (losing local commits)\n"
            f"3. Force push if needed\n\n"
            f"⚠️ WARNING: This may lose local commits!\n\n"
            f"Are you sure you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Get current branch name first
                branch_result = subprocess.run(
                    ['git', 'branch', '--show-current'],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if branch_result.returncode != 0:
                    QMessageBox.critical(self, "Error", "Could not determine current branch")
                    return
                
                current_branch = branch_result.stdout.strip()
                if not current_branch:
                    QMessageBox.critical(self, "Error", "Repository appears to be in detached HEAD state")
                    return
                
                # Execute force fix commands
                force_commands = [
                    'git fetch origin',
                    f'git reset --hard origin/{current_branch}'
                ]
                
                fix_result = GitDiagnostics.auto_fix_repository(
                    repo_path, 
                    'force_fix', 
                    force_commands
                )
                
                if fix_result['success']:
                    QMessageBox.information(
                        self,
                        "Force Fix Successful",
                        f"✅ {fix_result['message']}\n\nOutput:\n" + "\n".join(fix_result['output'][:10])
                    )
                    # Update button to show success
                    sender = self.sender()
                    sender.setText("✅ Force Fixed")
                    sender.setEnabled(False)
                    sender.setStyleSheet("background-color: #228B22; color: white;")
                    
                    # Auto-retry the operation
                    self.retry_operation()
                else:
                    QMessageBox.warning(
                        self,
                        "Force Fix Failed",
                        f"❌ {fix_result['message']}\n\nOutput:\n" + "\n".join(fix_result['output'][:10])
                    )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Force Fix Error",
                    f"Error during force fix: {str(e)}"
                )
    
    def perform_auto_fix(self):
        """Attempt to automatically fix the repository issue"""
        analysis = self.error_info['analysis']
        repo_path = self.error_info['repo_path']
        
        # Show confirmation dialog
        reply = QMessageBox.question(
            self, 
            "Confirm Auto-Fix",
            f"Attempt to automatically fix '{analysis['type']}' in repository?\n\n"
            f"Commands to be executed:\n" + "\n".join(f"• {cmd}" for cmd in analysis['commands']),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Perform the auto-fix
                fix_result = GitDiagnostics.auto_fix_repository(
                    repo_path, 
                    analysis['type'], 
                    analysis['commands']
                )
                
                if fix_result['success']:
                    QMessageBox.information(
                        self,
                        "Auto-Fix Successful",
                        f"✅ {fix_result['message']}\n\nOutput:\n" + "\n".join(fix_result['output'][:10])
                    )
                    # Update button to show success
                    sender = self.sender()
                    sender.setText("✅ Fixed")
                    sender.setEnabled(False)
                    sender.setStyleSheet("background-color: #228B22; color: white;")
                    
                    # Auto-retry the operation
                    self.retry_operation()
                else:
                    QMessageBox.warning(
                        self,
                        "Auto-Fix Failed",
                        f"❌ {fix_result['message']}\n\nOutput:\n" + "\n".join(fix_result['output'][:10])
                    )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Auto-Fix Error",
                    f"Error during auto-fix: {str(e)}"
                )
    
    def show_manual_commands(self):
        """Show manual commands for fixing the issue"""
        analysis = self.error_info['analysis']
        commands_text = "\n".join(analysis['commands'])
        
        QMessageBox.information(
            self,
            "Manual Fix Commands",
            f"To fix this issue manually, run these commands in the repository directory:\n\n{commands_text}\n\n"
            f"Repository path: {self.error_info['repo_path']}"
        )


class GitRepoManager(QMainWindow):
    """
    Main application window for Git Repository Manager
    """
    
    def __init__(self):
        super().__init__()
        self.repositories: List[Path] = []
        self.worker = None
        # Config file in same directory as script
        script_dir = Path(__file__).parent
        self.config_file = script_dir / "git_manager_config.json"
        self.error_widgets = []  # Store error fix widgets
        
        self.init_ui()
        self.load_configuration()
        self.scan_repositories()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Enhanced Git Repository Manager")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("Enhanced Git Repository Manager")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Configuration section
        config_group = QGroupBox("Configuration")
        config_layout = QHBoxLayout(config_group)
        
        self.config_label = QLabel("No directory configured")
        self.config_label.setStyleSheet("color: gray;")
        config_layout.addWidget(self.config_label)
        
        self.browse_button = QPushButton("Browse Directory")
        self.browse_button.clicked.connect(self.browse_directory)
        config_layout.addWidget(self.browse_button)
        
        layout.addWidget(config_group)
        
        # Repository list section
        repo_group = QGroupBox("Found Repositories")
        repo_layout = QVBoxLayout(repo_group)
        
        self.repo_list = QTextEdit()
        self.repo_list.setMaximumHeight(150)
        self.repo_list.setReadOnly(True)
        repo_layout.addWidget(self.repo_list)
        
        self.refresh_button = QPushButton("Refresh Repository List")
        self.refresh_button.clicked.connect(self.scan_repositories)
        repo_layout.addWidget(self.refresh_button)
        
        layout.addWidget(repo_group)
        
        # Action buttons with enhanced descriptions
        button_layout = QHBoxLayout()
        
        self.pull_button = QPushButton("Pull All Repositories\n(Safe: skips repos with uncommitted changes)")
        self.pull_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.pull_button.clicked.connect(self.pull_all)
        button_layout.addWidget(self.pull_button)
        
        self.push_button = QPushButton("Push All Repositories\n(Auto: add → commit → push)")
        self.push_button.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        self.push_button.clicked.connect(self.push_all)
        button_layout.addWidget(self.push_button)
        
        layout.addLayout(button_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status display
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        # Output area - Split into two sections
        output_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Success output (left side)
        success_group = QGroupBox("Successful Operations & Warnings")
        success_group.setStyleSheet("QGroupBox::title { color: green; font-weight: bold; }")
        success_layout = QVBoxLayout(success_group)
        
        self.success_text = QTextEdit()
        self.success_text.setReadOnly(True)
        self.success_text.setStyleSheet("background-color: #f0f8f0; border: 1px solid #90EE90;")
        success_layout.addWidget(self.success_text)
        
        # Add clear button for success output
        clear_success_btn = QPushButton("Clear Success Log")
        clear_success_btn.clicked.connect(self.success_text.clear)
        clear_success_btn.setStyleSheet("background-color: #90EE90; color: #006400;")
        success_layout.addWidget(clear_success_btn)
        
        output_splitter.addWidget(success_group)
        
        # Error output (right side) - Enhanced with fix widgets
        error_group = QGroupBox("Errors & Auto-Fix Solutions")
        error_group.setStyleSheet("QGroupBox::title { color: red; font-weight: bold; }")
        error_layout = QVBoxLayout(error_group)
        
        # Error text area (for simple error messages)
        self.error_text = QTextEdit()
        self.error_text.setReadOnly(True)
        self.error_text.setStyleSheet("background-color: #fff5f5; border: 1px solid #FFB6C1; color: #8B0000;")
        self.error_text.setMaximumHeight(150)
        error_layout.addWidget(self.error_text)
        
        # Smart fix area (for interactive error fixing)
        fix_area_label = QLabel("🔧 Smart Error Analysis & Auto-Fix")
        fix_area_label.setStyleSheet("font-weight: bold; color: #8B0000; background-color: #FFF8DC; padding: 5px; border: 1px solid #DDD;")
        error_layout.addWidget(fix_area_label)
        
        # Scrollable area for fix widgets
        self.fix_scroll_area = QScrollArea()
        self.fix_scroll_area.setWidgetResizable(True)
        self.fix_scroll_area.setStyleSheet("background-color: white; border: 1px solid #DDD;")
        
        self.fix_container = QWidget()
        self.fix_layout = QVBoxLayout(self.fix_container)
        self.fix_layout.addStretch()  # Push widgets to top
        
        self.fix_scroll_area.setWidget(self.fix_container)
        error_layout.addWidget(self.fix_scroll_area)
        
        # Control buttons for error area
        error_buttons = QHBoxLayout()
        
        clear_error_btn = QPushButton("Clear Error Log")
        clear_error_btn.clicked.connect(self.clear_error_area)
        clear_error_btn.setStyleSheet("background-color: #FFB6C1; color: #8B0000;")
        error_buttons.addWidget(clear_error_btn)
        
        health_check_btn = QPushButton("🏥 Health Check All")
        health_check_btn.clicked.connect(self.run_health_check)
        health_check_btn.setStyleSheet("background-color: #20B2AA; color: white;")
        error_buttons.addWidget(health_check_btn)
        
        retry_failed_btn = QPushButton("🔄 Retry All Failed")
        retry_failed_btn.clicked.connect(self.retry_failed_repositories)
        retry_failed_btn.setStyleSheet("background-color: #FF8C00; color: white; font-weight: bold;")
        error_buttons.addWidget(retry_failed_btn)
        
        error_buttons.addStretch()
        error_layout.addLayout(error_buttons)
        
        output_splitter.addWidget(error_group)
        
        # Set splitter proportions (60% success, 40% errors)
        output_splitter.setSizes([600, 400])
        
        layout.addWidget(output_splitter)
    
    def expand_environment_variables(self, path_str: str) -> str:
        """Expand environment variables in path string"""
        if not path_str:
            return path_str
        
        # Expand environment variables like $HOME, $USER, etc.
        expanded = os.path.expandvars(path_str)
        
        # Also expand ~ to home directory
        expanded = os.path.expanduser(expanded)
        
        return expanded
    
    def get_portable_path(self, absolute_path: str) -> str:
        """Convert absolute path to portable format using environment variables"""
        if not absolute_path:
            return absolute_path
        
        path = Path(absolute_path)
        home_dir = Path.home()
        
        try:
            # If path is under home directory, use $HOME
            relative_to_home = path.relative_to(home_dir)
            return f"$HOME/{relative_to_home}"
        except ValueError:
            # Path is not under home directory, return as-is
            return absolute_path
    
    def load_configuration(self):
        """Load configuration from JSON file with environment variable support"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    base_dir_raw = config.get('base_directory', '')
                    
                    if base_dir_raw:
                        # Expand environment variables
                        base_dir = self.expand_environment_variables(base_dir_raw)
                        
                        if os.path.exists(base_dir):
                            self.config_label.setText(f"Directory: {base_dir}")
                            self.config_label.setStyleSheet("color: green;")
                            return
                        else:
                            self.config_label.setText(f"Directory not found: {base_dir}")
                            self.config_label.setStyleSheet("color: orange;")
                            return
            
            # If no valid config, create default
            self.create_default_config()
            
        except Exception as e:
            self.show_error(f"Error loading configuration: {str(e)}")
            self.create_default_config()
    
    def create_default_config(self):
        """Create a default configuration file with portable paths"""
        # Use $HOME/git-repositories as default (portable across systems)
        default_config = {
            "base_directory": "$HOME/git-repositories",
            "description": "Base directory containing git repositories. Use $HOME, $USER, etc. for portability across systems.",
            "examples": {
                "home_projects": "$HOME/projects", 
                "user_documents": "$HOME/Documents/git-repos",
                "custom_path": "/absolute/path/to/repos"
            }
        }
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            
            # Check if default directory exists
            expanded_default = self.expand_environment_variables(default_config["base_directory"])
            if os.path.exists(expanded_default):
                self.config_label.setText(f"Using default: {expanded_default}")
                self.config_label.setStyleSheet("color: green;")
            else:
                self.config_label.setText("Please configure base directory (default path doesn't exist)")
                self.config_label.setStyleSheet("color: red;")
                
        except Exception as e:
            self.show_error(f"Error creating configuration file: {str(e)}")
    
    def browse_directory(self):
        """Open dialog to select base directory and save in portable format"""
        directory = QFileDialog.getExistingDirectory(
            self, 
            "Select Directory Containing Git Repositories"
        )
        
        if directory:
            # Convert to portable path using environment variables when possible
            portable_path = self.get_portable_path(directory)
            
            # Update configuration with portable path
            config = {
                "base_directory": portable_path,
                "description": "Base directory containing git repositories. Use $HOME, $USER, etc. for portability across systems.",
                "expanded_path": directory,  # Store expanded path for reference
                "examples": {
                    "home_projects": "$HOME/projects", 
                    "user_documents": "$HOME/Documents/git-repos",
                    "custom_path": "/absolute/path/to/repos"
                }
            }
            
            try:
                with open(self.config_file, 'w') as f:
                    json.dump(config, f, indent=2)
                
                self.config_label.setText(f"Directory: {directory}")
                if portable_path != directory:
                    self.config_label.setText(f"Directory: {directory}\n(Saved as: {portable_path})")
                self.config_label.setStyleSheet("color: green;")
                
                # Refresh repository list
                self.scan_repositories()
                
            except Exception as e:
                self.show_error(f"Error saving configuration: {str(e)}")
    
    def scan_repositories(self):
        """Recursively scan base directory for git repositories at any depth"""
        try:
            # Load current configuration
            if not self.config_file.exists():
                self.repo_list.setText("No configuration file found. Please browse for a directory.")
                return
            
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                base_dir_raw = config.get('base_directory', '')
            
            if not base_dir_raw:
                self.repo_list.setText("No base directory configured. Please browse for a directory.")
                return
            
            # Expand environment variables
            base_dir = self.expand_environment_variables(base_dir_raw)
            
            if not os.path.exists(base_dir):
                self.repo_list.setText(f"Base directory does not exist: {base_dir}\n(From config: {base_dir_raw})")
                return
            
            # Find all git repositories recursively
            self.repositories = []
            base_path = Path(base_dir)
            
            self.status_label.setText("Scanning for repositories...")
            
            # Use rglob to recursively find all .git directories
            for git_dir in base_path.rglob('.git'):
                if git_dir.is_dir():
                    # The parent of .git directory is the repository root
                    repo_path = git_dir.parent
                    self.repositories.append(repo_path)
            
            # Sort repositories by path for consistent display
            self.repositories.sort(key=lambda x: str(x).lower())
            
            # Update display
            if self.repositories:
                # Create relative paths for better display
                repo_display = []
                for repo in self.repositories:
                    try:
                        # Show path relative to base directory
                        relative_path = repo.relative_to(base_path)
                        repo_display.append(f"• {relative_path}")
                    except ValueError:
                        # Fallback to absolute path if relative fails
                        repo_display.append(f"• {repo.name}")
                
                self.repo_list.setText('\n'.join(repo_display))
                
                # Show config info in status
                config_info = f"Found {len(self.repositories)} git repositories"
                if base_dir_raw != base_dir:
                    config_info += f" (expanded from {base_dir_raw})"
                
                self.status_label.setText(config_info)
                self.status_label.setStyleSheet("")  # Reset any previous styling
                
                # Enable buttons
                self.pull_button.setEnabled(True)
                self.push_button.setEnabled(True)
            else:
                self.repo_list.setText("No git repositories found in the specified directory tree.")
                self.status_label.setText("No repositories found")
                
                # Disable buttons
                self.pull_button.setEnabled(False)
                self.push_button.setEnabled(False)
                
        except Exception as e:
            self.show_error(f"Error scanning repositories: {str(e)}")
    
    def pull_all(self):
        """Pull changes from all repositories (safe mode)"""
        self.execute_git_operation('pull')
    
    def push_all(self):
        """Push changes to all repositories (with auto add/commit)"""
        self.execute_git_operation('push')
    
    def execute_git_operation(self, operation: str):
        """Execute git operation on all repositories"""
        if not self.repositories:
            self.show_error("No repositories found. Please scan for repositories first.")
            return
        
        # Disable buttons during operation
        self.pull_button.setEnabled(False)
        self.push_button.setEnabled(False)
        self.refresh_button.setEnabled(False)
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        operation_desc = "pull (safe mode)" if operation == 'pull' else "push (auto add/commit)"
        self.status_label.setText(f"Executing {operation_desc} operation...")
        self.status_label.setStyleSheet("")  # Reset any previous styling
        
        # Clear previous output
        self.success_text.clear()
        self.clear_error_area()
        
        # Create and start worker thread
        self.worker = GitWorker(self.repositories, operation)
        self.worker.progress.connect(self.update_progress)
        self.worker.success_output.connect(self.add_success_message)
        self.worker.error_output.connect(self.add_error_with_fix)
        self.worker.finished.connect(self.operation_finished)
        self.worker.start()
    
    def update_progress(self, message: str):
        """Update progress display"""
        self.status_label.setText(message)
    
    def add_success_message(self, message: str):
        """Add message to success output area"""
        self.success_text.append(message)
        # Auto-scroll to bottom
        scrollbar = self.success_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def add_error_with_fix(self, error_message: str, error_info: Dict):
        """Add error message with auto-fix capabilities"""
        # Add basic error to text area
        self.error_text.append(error_message)
        scrollbar = self.error_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        # Add smart fix widget if fix is available
        if error_info['analysis']['fix_available'] or error_info['analysis']['type'] != 'unknown':
            fix_widget = ErrorFixWidget(error_info)
            
            # Connect retry signal
            fix_widget.retry_requested.connect(self.retry_single_repository)
            
            # Remove the stretch item temporarily
            self.fix_layout.removeItem(self.fix_layout.itemAt(self.fix_layout.count() - 1))
            
            # Add the fix widget
            self.fix_layout.addWidget(fix_widget)
            self.error_widgets.append(fix_widget)
            
            # Re-add stretch to keep widgets at top
            self.fix_layout.addStretch()
            
            # Scroll to show new widget
            # Scroll to show new widget
            self.fix_scroll_area.ensureWidgetVisible(fix_widget)
    
    def retry_failed_repositories(self):
        """Retry operation on all repositories that had errors"""
        if not self.error_widgets:
            QMessageBox.information(self, "No Failed Repositories", "No repositories with errors to retry.")
            return
        
        # Extract repository paths from error widgets
        failed_repos = []
        for widget in self.error_widgets:
            repo_path = widget.error_info['repo_path']
            if repo_path not in failed_repos:
                failed_repos.append(repo_path)
        
        if not failed_repos:
            QMessageBox.information(self, "No Failed Repositories", "No repositories with errors to retry.")
            return
        
        # Ask for confirmation
        repo_names = [repo.name for repo in failed_repos]
        reply = QMessageBox.question(
            self,
            "Retry Failed Repositories",
            f"Retry operation on {len(failed_repos)} failed repositories?\n\n"
            f"Repositories: {', '.join(repo_names[:5])}{'...' if len(repo_names) > 5 else ''}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Clear existing errors
            self.clear_error_area()
            
            # Determine operation (default to push, could be made smarter)
            operation = 'push'
            
            # Start retry operation
            self.pull_button.setEnabled(False)
            self.push_button.setEnabled(False)
            self.refresh_button.setEnabled(False)
            
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)
            self.status_label.setText(f"Retrying {operation} on {len(failed_repos)} repositories...")
            self.status_label.setStyleSheet("color: #FF8C00; font-weight: bold;")
            
            # Create worker for failed repositories
            self.worker = GitWorker(failed_repos, operation)
            self.worker.progress.connect(self.update_progress)
            self.worker.success_output.connect(self.add_success_message)
            self.worker.error_output.connect(self.add_error_with_fix)
            self.worker.finished.connect(self.operation_finished)
            self.worker.start()
    
    def retry_single_repository(self, repo_path_str: str):
        """Retry operation on a single repository"""
        repo_path = Path(repo_path_str)
        
        if repo_path not in self.repositories:
            QMessageBox.warning(self, "Repository Not Found", f"Repository {repo_path} not found in current list.")
            return
        
        # Determine last operation (could be enhanced to track this)
        operation = 'push'  # Default to push, could be made smarter
        
        # Create worker for single repository
        self.pull_button.setEnabled(False)
        self.push_button.setEnabled(False)
        self.refresh_button.setEnabled(False)
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_label.setText(f"Retrying operation on {repo_path.name}...")
        self.status_label.setStyleSheet("color: #FF8C00; font-weight: bold;")
        
        # Create worker for single repository
        self.worker = GitWorker([repo_path], operation)
        self.worker.progress.connect(self.update_progress)
        self.worker.success_output.connect(self.add_success_message)
        self.worker.error_output.connect(self.add_error_with_fix)
        self.worker.finished.connect(self.operation_finished)
        self.worker.start()
    
    def clear_error_area(self):
        """Clear all error messages and fix widgets"""
        self.error_text.clear()
        
        # Remove all fix widgets
        for widget in self.error_widgets:
            widget.setParent(None)
        self.error_widgets.clear()
        
        # Clear the layout (except stretch)
        while self.fix_layout.count() > 1:
            child = self.fix_layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)
    
    def run_health_check(self):
        """Run health check on all repositories"""
        if not self.repositories:
            self.show_error("No repositories found. Please scan for repositories first.")
            return
        
        self.status_label.setText("Running health checks...")
        self.status_label.setStyleSheet("color: #20B2AA; font-weight: bold;")
        
        health_report = []
        issues_found = 0
        
        for repo_path in self.repositories:
            repo_display = str(repo_path.name)
            if len(repo_path.parts) > 2:
                repo_display = "/".join(repo_path.parts[-2:])
            
            health_info = GitDiagnostics.check_repository_health(repo_path)
            
            if not health_info['healthy']:
                issues_found += 1
                health_report.append(f"❌ {repo_display}: {', '.join(health_info['issues'])}")
            elif health_info['warnings']:
                health_report.append(f"⚠️ {repo_display}: {', '.join(health_info['warnings'])}")
            else:
                health_report.append(f"✅ {repo_display}: Healthy")
        
        # Display health report
        if issues_found == 0:
            self.status_label.setText(f"✅ Health check complete - All repositories healthy!")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.status_label.setText(f"⚠️ Health check complete - {issues_found} issues found")
            self.status_label.setStyleSheet("color: orange; font-weight: bold;")
        
        # Show detailed report
        QMessageBox.information(
            self,
            "Repository Health Report",
            f"Health Check Results:\n\n" + "\n".join(health_report)
        )
    
    def operation_finished(self):
        """Handle completion of git operation"""
        # Hide progress bar
        self.progress_bar.setVisible(False)
        
        # Update status with summary
        success_count = self.success_text.toPlainText().count('✓')
        warning_count = self.success_text.toPlainText().count('⚠')
        error_count = self.error_text.toPlainText().count('✗')
        fixable_errors = len(self.error_widgets)
        
        if error_count == 0:
            if warning_count > 0:
                self.status_label.setText(f"✅ Operation completed! ({success_count} successful, {warning_count} warnings)")
                self.status_label.setStyleSheet("color: green; font-weight: bold;")
            else:
                self.status_label.setText(f"✅ Operation completed successfully! ({success_count} repositories)")
                self.status_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            status_msg = f"⚠️ Completed: {success_count} successful"
            if warning_count > 0:
                status_msg += f", {warning_count} warnings"
            status_msg += f", {error_count} errors"
            if fixable_errors > 0:
                status_msg += f" ({fixable_errors} auto-fixable)"
            self.status_label.setText(status_msg)
            self.status_label.setStyleSheet("color: orange; font-weight: bold;")
        
        # Re-enable buttons
        self.pull_button.setEnabled(True)
        self.push_button.setEnabled(True)
        self.refresh_button.setEnabled(True)
        
        # Clean up worker
        self.worker = None
    
    def show_error(self, error_message: str):
        """Display error message to user"""
        QMessageBox.critical(self, "Error", error_message)
        self.status_label.setText("Error occurred")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        
        # Re-enable buttons
        self.pull_button.setEnabled(True)
        self.push_button.setEnabled(True)
        self.refresh_button.setEnabled(True)
        
        # Hide progress bar
        self.progress_bar.setVisible(False)


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Enhanced Git Repository Manager")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("Educational Software")
    
    # Create and show main window
    window = GitRepoManager()
    window.show()
    
    # Start event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()