"""Git synchronization module for backing up data to GitHub."""
from __future__ import annotations

import logging
import os
import base64
from typing import Optional
from pathlib import Path

from git import Repo, GitCommandError
from git.exc import InvalidGitRepositoryError

logger = logging.getLogger(__name__)


class GitSyncError(Exception):
    """Base exception for git sync errors."""

    pass


class GitAuthError(GitSyncError):
    """Authentication failed with git remote."""

    pass


class GitMergeConflictError(GitSyncError):
    """Merge conflict occurred during pull/push."""

    pass


class GitSync:
    """Manages git operations for data synchronization with GitHub."""

    def __init__(
        self,
        data_dir: str,
        repo_url: str,
        ssh_key_path: Optional[str] = None,
        github_token: Optional[str] = None,
        author_name: str = "Data Sync",
        author_email: str = "sync@example.com",
    ):
        """Initialize GitSync manager.

        Args:
            data_dir: Path to the data directory to sync (contains players.json, games.json, assets/)
            repo_url: GitHub repository URL (SSH: git@github.com:user/repo.git or HTTPS: https://github.com/user/repo.git)
            ssh_key_path: Path to SSH private key (optional, for SSH auth, defaults to ~/.ssh/id_rsa)
            github_token: GitHub Personal Access Token (optional, for HTTPS auth)
            author_name: Git commit author name
            author_email: Git commit author email
        """
        self.data_dir = Path(data_dir)
        self.repo_url = repo_url
        self.ssh_key_path = ssh_key_path or os.path.expanduser("~/.ssh/id_rsa")
        self.github_token = github_token
        self.author_name = author_name
        self.author_email = author_email
        self.repo: Optional[Repo] = None
        self.auth_method = self._determine_auth_method()
        self._setup_auth()

    def _determine_auth_method(self) -> str:
        """Determine which auth method to use: 'ssh', 'https_token', or 'https_basic'."""
        if self.github_token:
            return "https_token"
        elif self.repo_url.startswith("git@"):
            return "ssh"
        elif self.repo_url.startswith("https://"):
            return "https_basic"
        else:
            # Default to SSH if ambiguous
            return "ssh"

    def _setup_auth(self) -> None:
        """Configure authentication for git operations."""
        if self.auth_method == "ssh":
            self._setup_ssh()
        elif self.auth_method == "https_token":
            self._setup_https_token()

    def _setup_ssh(self) -> None:
        """Configure SSH environment for git operations (SSH key authentication)."""
        if not os.path.exists(self.ssh_key_path):
            logger.warning(
                f"SSH key not found at {self.ssh_key_path}. "
                "Please ensure it exists before attempting git operations."
            )

        # Set GIT_SSH_COMMAND to use specific key
        ssh_cmd = f"ssh -i {self.ssh_key_path} -o StrictHostKeyChecking=no"
        os.environ["GIT_SSH_COMMAND"] = ssh_cmd

    def _setup_https_token(self) -> None:
        """Configure HTTPS authentication using GitHub Personal Access Token."""
        if not self.github_token:
            raise GitAuthError("GitHub token not provided")

        credentials = base64.b64encode(
            f"x-access-token:{self.github_token}".encode()
        ).decode()
        config_index = os.environ.get("GIT_GITHUB_PAT_CONFIG_INDEX")
        if not config_index:
            config_index = os.environ.get("GIT_CONFIG_COUNT") or "0"
            os.environ["GIT_GITHUB_PAT_CONFIG_INDEX"] = config_index
            os.environ["GIT_CONFIG_COUNT"] = str(int(config_index) + 1)

        os.environ[f"GIT_CONFIG_KEY_{config_index}"] = (
            "http.https://github.com/.extraheader"
        )
        os.environ[f"GIT_CONFIG_VALUE_{config_index}"] = (
            f"AUTHORIZATION: basic {credentials}"
        )
        os.environ["GIT_TERMINAL_PROMPT"] = "0"
        logger.debug("Configured GitHub HTTPS token authentication")

    def _initialize_repo(self) -> None:
        """Initialize local git repository if it doesn't exist."""
        if self.repo is not None:
            return

        try:
            self.repo = Repo(self.data_dir)
            logger.info(f"Opened existing repository at {self.data_dir}")
            self._configure_repo()
            self._add_remote()
        except InvalidGitRepositoryError:
            logger.info(f"Initializing new repository at {self.data_dir}")
            self.data_dir.mkdir(parents=True, exist_ok=True)
            self.repo = Repo.init(self.data_dir)
            self._configure_repo()
            self._add_remote()

    def _configure_repo(self) -> None:
        """Configure git author for commits."""
        if self.repo is None:
            return

        with self.repo.config_writer() as git_config:
            git_config.set_value("user", "name", self.author_name)
            git_config.set_value("user", "email", self.author_email)

    def _add_remote(self) -> None:
        """Add origin remote if it doesn't exist."""
        if self.repo is None:
            return

        try:
            origin = self.repo.remote("origin")
            if origin.url != self.repo_url:
                logger.info("Updating origin remote URL")
                self.repo.git.remote("set-url", "origin", self.repo_url)
            else:
                logger.info("Origin remote already exists")
        except ValueError:
            logger.info(f"Adding remote origin: {self.repo_url}")
            self.repo.create_remote("origin", self.repo_url)

    def clone_or_pull(self) -> dict:
        """Clone repository if needed, otherwise pull latest changes.

        Returns:
            Status dict with 'action' (clone/pull), 'success' (bool), 'message' (str)

        Raises:
            GitAuthError: If SSH authentication fails
            GitSyncError: For other git errors
        """
        self._initialize_repo()

        if self.repo is None:
            raise GitSyncError("Failed to initialize repository")

        try:
            # Check if this is a fresh repository with no commits
            if len(self.repo.heads) == 0:
                logger.info("No commits found, cloning from remote")
                return self._clone_from_remote()
            else:
                logger.info("Repository exists, pulling latest changes")
                return self._pull_from_remote()
        except GitCommandError as e:
            if "auth" in str(e).lower() or "permission" in str(e).lower():
                logger.error(f"SSH authentication failed: {e}")
                raise GitAuthError(f"SSH authentication failed: {e}") from e
            logger.error(f"Git operation failed: {e}")
            raise GitSyncError(f"Git operation failed: {e}") from e

    def _clone_from_remote(self) -> dict:
        """Clone repository contents from remote."""
        if self.repo is None:
            raise GitSyncError("Repository not initialized")

        try:
            origin = self.repo.remote("origin")
            origin.fetch()

            default_branch = None
            try:
                remote_head = self.repo.git.symbolic_ref(
                    "refs/remotes/origin/HEAD"
                )
                default_branch = remote_head.removeprefix("refs/remotes/origin/")
            except GitCommandError:
                pass

            if not default_branch:
                for branch_name in ("main", "master"):
                    if f"origin/{branch_name}" in self.repo.refs:
                        default_branch = branch_name
                        break

            if not default_branch:
                raise GitSyncError("Remote has no default branch to check out")

            remote_ref = f"origin/{default_branch}"
            self.repo.git.checkout("-B", default_branch, remote_ref)
            self.repo.git.branch(
                "--set-upstream-to", remote_ref, default_branch
            )
            logger.info(
                "Successfully initialized local branch from %s", remote_ref
            )
            return {
                "action": "clone",
                "success": True,
                "message": "Cloned latest data from remote",
            }
        except GitCommandError as e:
            logger.error(f"Clone/pull failed: {e}")
            raise GitSyncError(f"Failed to clone/pull from remote: {e}") from e

    def _pull_from_remote(self) -> dict:
        """Pull latest changes from remote."""
        if self.repo is None:
            raise GitSyncError("Repository not initialized")

        try:
            origin = self.repo.remote("origin")
            origin.pull()
            logger.info("Successfully pulled from remote")
            return {
                "action": "pull",
                "success": True,
                "message": "Pulled latest data from remote",
            }
        except GitCommandError as e:
            if "CONFLICT" in str(e):
                logger.error(f"Merge conflict during pull: {e}")
                raise GitMergeConflictError(
                    f"Merge conflict occurred during pull: {e}"
                ) from e
            logger.error(f"Pull failed: {e}")
            raise GitSyncError(f"Failed to pull from remote: {e}") from e

    def push(self, message: str = "Auto-sync data changes") -> dict:
        """Stage all changes and push to remote.

        Strategy: Pull before push (optimistic locking)
        1. Fetch from remote to detect divergence
        2. If local differs from remote, pull and merge
        3. After merge succeeds, push changes

        Args:
            message: Commit message

        Returns:
            Status dict with 'success' (bool), 'message' (str), 'commit_sha' (str)

        Raises:
            GitMergeConflictError: If merge conflict occurs
            GitAuthError: If SSH authentication fails
            GitSyncError: For other git errors
        """
        self._initialize_repo()

        if self.repo is None:
            raise GitSyncError("Repository not initialized")

        try:
            # Stage all changes
            self.repo.git.add(A=True)

            # Check if there's anything to commit
            # On first commit, HEAD doesn't exist, so check for untracked files
            try:
                has_changes = bool(self.repo.index.diff("HEAD")) or bool(self.repo.untracked_files)
            except ValueError:
                # HEAD doesn't exist yet (first commit), check if there are files to commit
                has_changes = bool(self.repo.index.entries) or bool(self.repo.untracked_files)

            if has_changes:
                logger.info("Changes detected, committing...")
                commit = self.repo.index.commit(message)
                logger.info(f"Committed: {commit.hexsha[:8]}")
            else:
                logger.info("No changes to commit")
                return {
                    "success": True,
                    "message": "No changes to commit",
                    "commit_sha": None,
                }

            # Fetch remote to check for divergence
            origin = self.repo.remote("origin")
            origin.fetch()

            # Try to push (use -u to set upstream on first push)
            logger.info("Pushing to remote...")
            try:
                origin.push()
            except GitCommandError as e:
                # On first push to empty remote, might need to create the branch
                if "no upstream" in str(e).lower() or "rejected" in str(e).lower():
                    logger.info("First push detected, setting upstream branch...")
                    self.repo.git.push("-u", "origin", self.repo.active_branch.name)
                else:
                    raise
            logger.info("Successfully pushed to remote")

            return {
                "success": True,
                "message": "Changes committed and pushed successfully",
                "commit_sha": commit.hexsha,
            }

        except GitCommandError as e:
            error_str = str(e)

            # Check for authentication errors
            if "auth" in error_str.lower() or "permission" in error_str.lower():
                logger.error(f"SSH authentication failed: {e}")
                raise GitAuthError(f"SSH authentication failed: {e}") from e

            # Check for divergence/fast-forward errors
            if "failed to push" in error_str.lower() or "rejected" in error_str.lower():
                logger.warning("Local branch diverged from remote, attempting merge...")
                try:
                    return self._pull_and_retry_push(message)
                except GitMergeConflictError:
                    raise
                except Exception as retry_error:
                    logger.error(f"Retry failed: {retry_error}")
                    raise GitSyncError(f"Failed to push after merge: {retry_error}") from retry_error

            logger.error(f"Push failed: {e}")
            raise GitSyncError(f"Failed to push to remote: {e}") from e

    def _pull_and_retry_push(self, message: str) -> dict:
        """Pull remote changes and retry push.

        Args:
            message: Commit message for potential auto-merge commit

        Returns:
            Status dict with 'success' (bool), 'message' (str), 'commit_sha' (str)

        Raises:
            GitMergeConflictError: If merge conflict occurs
        """
        if self.repo is None:
            raise GitSyncError("Repository not initialized")

        try:
            origin = self.repo.remote("origin")
            logger.info("Pulling remote changes...")
            origin.pull()
            logger.info("Pull succeeded, retrying push...")
            origin.push()
            logger.info("Push succeeded after merge")

            return {
                "success": True,
                "message": "Pulled remote changes, merged, and pushed successfully",
                "commit_sha": self.repo.head.commit.hexsha,
            }

        except GitCommandError as e:
            if "CONFLICT" in str(e):
                logger.error(f"Merge conflict: {e}")
                # Reset to remote state on conflict
                self.reset_to_remote()
                raise GitMergeConflictError(
                    f"Merge conflict occurred. Local changes have been discarded. "
                    f"Please retry your operation. Details: {e}"
                ) from e

            raise GitSyncError(f"Failed to pull and retry: {e}") from e

    def reset_to_remote(self) -> None:
        """Reset local repository to match remote (hard reset).

        Used for conflict recovery.
        """
        if self.repo is None:
            self._initialize_repo()

        if self.repo is None:
            raise GitSyncError("Repository not initialized")

        try:
            logger.warning("Performing hard reset to remote/main...")
            origin = self.repo.remote("origin")
            origin.fetch()

            # Determine default branch (main or master)
            default_branch = None
            for ref in origin.refs:
                if ref.name in ("origin/main", "origin/master"):
                    default_branch = ref.name.replace("origin/", "")
                    break

            if not default_branch:
                # Fallback: use first available branch
                default_branch = (
                    self.repo.heads[0].name
                    if self.repo.heads
                    else "main"
                )

            self.repo.git.reset("--hard", f"origin/{default_branch}")
            logger.info(f"Hard reset to origin/{default_branch}")

        except GitCommandError as e:
            logger.error(f"Hard reset failed: {e}")
            raise GitSyncError(f"Failed to reset to remote: {e}") from e

    def get_status(self) -> dict:
        """Get current sync status.

        Returns:
            Status dict with 'ahead', 'behind', 'conflicted', 'dirty'
        """
        self._initialize_repo()

        if self.repo is None:
            return {
                "ahead": 0,
                "behind": 0,
                "conflicted": False,
                "dirty": False,
            }

        try:
            # Check for uncommitted changes
            dirty = bool(self.repo.is_dirty(untracked_files=True))

            # Check for unmerged paths (conflicts)
            conflicted = bool(self.repo.index.unmerged_blobs())

            # Count ahead/behind
            ahead = 0
            behind = 0
            try:
                origin = self.repo.remote("origin")
                origin.fetch()

                # Get tracking branch
                if self.repo.active_branch.tracking_branch():
                    tracking = self.repo.active_branch.tracking_branch()
                    commits_ahead = list(
                        self.repo.iter_commits(f"{tracking}..HEAD")
                    )
                    commits_behind = list(
                        self.repo.iter_commits(f"HEAD..{tracking}")
                    )
                    ahead = len(commits_ahead)
                    behind = len(commits_behind)
            except (GitCommandError, ValueError):
                # No tracking branch or remote not accessible
                pass

            return {
                "ahead": ahead,
                "behind": behind,
                "conflicted": conflicted,
                "dirty": dirty,
            }

        except Exception as e:
            logger.warning(f"Failed to get status: {e}")
            return {
                "ahead": 0,
                "behind": 0,
                "conflicted": False,
                "dirty": False,
            }
