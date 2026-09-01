#!/usr/bin/env python3
"""
Migration script to initialize GitHub-based version control for data.

Usage:
    python scripts/migrate_to_github.py --repo-url <URL> --author-name <name> --author-email <email>

Example:
    python scripts/migrate_to_github.py \
        --repo-url git@github.com:username/sh_stats_gui-data.git \
        --author-name "Game Stats" \
        --author-email "stats@example.com"

Prerequisites:
    1. Create empty GitHub repository (sh_stats_gui-data or similar)
    2. SSH key configured and added to GitHub
    3. Test SSH access: ssh -T git@github.com
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.git_sync import GitSync

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def verify_ssh_access(repo_url: str) -> bool:
    """Verify SSH access to the repository."""
    try:
        import subprocess

        # Extract host from repo URL (git@github.com:user/repo.git)
        if "git@" in repo_url:
            # Extract the full git@host part
            git_host = repo_url.split(":")[0]  # git@github.com
        else:
            logger.error("Only SSH URLs are supported (git@github.com:user/repo.git)")
            return False

        logger.info(f"Testing SSH connection to {git_host}...")
        result = subprocess.run(
            ["ssh", "-T", git_host],
            capture_output=True,
            timeout=5,
        )

        # GitHub returns exit code 1 with success message, check both stdout and stderr
        output = (result.stdout + result.stderr).decode().lower()
        if "successfully authenticated" in output or "authenticated" in output:
            logger.info("✓ SSH authentication successful")
            return True
        elif "denied" in output or "permission" in output:
            logger.error("✗ SSH authentication failed. Check your SSH key and GitHub setup.")
            return False
        else:
            # Assume success if no auth error
            logger.info("✓ SSH connection OK")
            return True

    except Exception as e:
        logger.error(f"✗ SSH test failed: {e}")
        logger.info("Please ensure:")
        logger.info("  1. SSH key is generated: ssh-keygen -t ed25519")
        logger.info("  2. Public key added to GitHub: https://github.com/settings/keys")
        logger.info("  3. SSH access works: ssh -T git@github.com")
        return False


def verify_pat_access(repo_url: str, token: str) -> bool:
    """Verify GitHub Personal Access Token (PAT) access."""
    try:
        import subprocess
        
        # Convert HTTPS URL to include token
        if repo_url.startswith("https://"):
            # Extract the URL part after https://
            url_part = repo_url[8:]  # Remove "https://"
            auth_url = f"https://git:{token}@{url_part}"
        else:
            logger.error("PAT authentication requires HTTPS URL (https://github.com/user/repo.git)")
            return False
        
        logger.info("Testing PAT access to repository...")
        result = subprocess.run(
            ["git", "ls-remote", "--heads", auth_url],
            capture_output=True,
            timeout=5,
        )
        
        if result.returncode == 0:
            logger.info("✓ PAT authentication successful")
            return True
        else:
            error_output = result.stderr.decode().lower()
            if "denied" in error_output or "forbidden" in error_output or "unauthorized" in error_output:
                logger.error("✗ PAT authentication failed. Check your token and permissions.")
            else:
                logger.error(f"✗ Repository access failed: {result.stderr.decode()}")
            return False
    
    except Exception as e:
        logger.error(f"✗ PAT test failed: {e}")
        logger.info("Please ensure:")
        logger.info("  1. GitHub PAT is valid and not expired")
        logger.info("  2. PAT has 'repo' scope enabled")
        logger.info("  3. Repository URL is correct (HTTPS format)")
        return False


def migrate_to_github(
    repo_url: str,
    author_name: str = "Data Sync",
    author_email: str = "sync@example.com",
    ssh_key_path: str | None = None,
    github_token: str | None = None,
) -> bool:
    """Migrate existing data to GitHub repository.

    Supports two authentication methods:
    1. SSH: repo_url (SSH format) + ssh_key_path (optional, defaults to ~/.ssh/id_rsa)
    2. HTTPS with PAT: repo_url (HTTPS format) + github_token (required)

    Args:
        repo_url: GitHub repository URL (SSH: git@github.com:user/repo.git or HTTPS: https://github.com/user/repo.git)
        author_name: Git commit author name
        author_email: Git commit author email
        ssh_key_path: Path to SSH private key (optional, for SSH auth)
        github_token: GitHub Personal Access Token (optional, for HTTPS auth)

    Returns:
        True if migration succeeded, False otherwise
    """
    workspace_root = Path(__file__).parent.parent
    data_dir = workspace_root / "data"

    logger.info(f"Starting migration of {data_dir}")
    logger.info(f"Repository URL: {repo_url}")

    # Verify authentication based on repo URL format
    if repo_url.startswith("git@"):
        logger.info("Authentication method: SSH")
        if not verify_ssh_access(repo_url):
            return False
    elif repo_url.startswith("https://"):
        logger.info("Authentication method: HTTPS with PAT")
        if not github_token:
            logger.error("GitHub PAT token is required for HTTPS authentication")
            return False
        if not verify_pat_access(repo_url, github_token):
            return False
    else:
        logger.error("Repository URL must be SSH (git@github.com:...) or HTTPS (https://github.com/...)")
        return False

    # Initialize git sync
    try:
        git_sync = GitSync(
            data_dir=str(data_dir),
            repo_url=repo_url,
            ssh_key_path=ssh_key_path,
            github_token=github_token,
            author_name=author_name,
            author_email=author_email,
        )
        logger.info("✓ GitSync initialized")
    except Exception as e:
        logger.error(f"✗ Failed to initialize GitSync: {e}")
        return False

    # Verify data exists
    players_file = data_dir / "players.json"
    games_file = data_dir / "games.json"
    avatars_dir = data_dir.parent / "assets" / "avatars"

    logger.info(f"Checking data files...")
    if players_file.exists():
        logger.info(f"  ✓ Found players.json ({players_file.stat().st_size} bytes)")
    else:
        logger.warning(f"  ⚠ players.json not found (will be created empty)")

    if games_file.exists():
        logger.info(f"  ✓ Found games.json ({games_file.stat().st_size} bytes)")
    else:
        logger.warning(f"  ⚠ games.json not found (will be created empty)")

    if avatars_dir.exists():
        avatar_count = len(list(avatars_dir.glob("*")))
        logger.info(f"  ✓ Found {avatar_count} avatar files")
    else:
        logger.warning(f"  ⚠ No avatars directory found")

    # Create initial commit
    try:
        logger.info("\nPushing initial data to repository...")
        result = git_sync.push("Initial data commit")
        logger.info(f"✓ Push successful: {result['message']}")
        if result.get("commit_sha"):
            logger.info(f"  Commit SHA: {result['commit_sha'][:8]}")
    except Exception as e:
        logger.error(f"✗ Push failed: {e}")
        logger.info("\nTroubleshooting:")
        logger.info("  1. Verify SSH key is accessible: ls -la ~/.ssh/")
        logger.info("  2. Test SSH: ssh -T git@github.com")
        logger.info("  3. Ensure repository is empty on GitHub")
        logger.info("  4. Check repo URL is correct")
        return False

    # Verify round-trip
    logger.info("\nVerifying sync status...")
    try:
        status = git_sync.get_status()
        logger.info(f"  Ahead: {status['ahead']}, Behind: {status['behind']}")
        logger.info(f"  Dirty: {status['dirty']}, Conflicts: {status['conflicted']}")
        if status["ahead"] == 0 and status["behind"] == 0:
            logger.info("✓ Repository is in sync")
        else:
            logger.warning("⚠ Repository status may need attention")
    except Exception as e:
        logger.warning(f"⚠ Could not verify status: {e}")

    logger.info("\n" + "=" * 60)
    logger.info("✓ MIGRATION SUCCESSFUL!")
    logger.info("=" * 60)
    logger.info("\nNext steps:")
    logger.info("  1. Set environment variables:")
    logger.info(f"     export GIT_DATA_REPO_URL='{repo_url}'")
    logger.info(f"     export GIT_AUTHOR_NAME='{author_name}'")
    logger.info(f"     export GIT_AUTHOR_EMAIL='{author_email}'")
    if github_token:
        logger.info(f"     export GIT_GITHUB_TOKEN='{github_token}'")
    if ssh_key_path:
        logger.info(f"     export GIT_SSH_KEY_PATH='{ssh_key_path}'")
    logger.info("\n  2. Or create .github-sync-config with these values")
    logger.info("  3. Restart the backend server")
    logger.info("  4. Verify frontend can sync: check browser console for /api/sync/pull")

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Migrate data to GitHub repository with git sync",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--repo-url",
        required=True,
        help="GitHub repository URL (SSH: git@github.com:user/repo.git or HTTPS: https://github.com/user/repo.git)",
    )
    parser.add_argument(
        "--author-name",
        default="Data Sync",
        help="Git commit author name (default: Data Sync)",
    )
    parser.add_argument(
        "--author-email",
        default="sync@example.com",
        help="Git commit author email (default: sync@example.com)",
    )
    parser.add_argument(
        "--ssh-key-path",
        help="Path to SSH private key (optional, for SSH auth, defaults to ~/.ssh/id_rsa)",
    )
    parser.add_argument(
        "--github-token",
        help="GitHub Personal Access Token (required for HTTPS repo URLs)",
    )

    args = parser.parse_args()

    success = migrate_to_github(
        repo_url=args.repo_url,
        author_name=args.author_name,
        author_email=args.author_email,
        ssh_key_path=args.ssh_key_path,
        github_token=args.github_token,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
