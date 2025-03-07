"""Repository cloning functionality."""

import subprocess
from pathlib import Path
from urllib.parse import urlparse

from wish_knowledge_loader.settings import Settings


class RepoCloner:
    """Class for cloning GitHub repositories."""

    def __init__(self, settings: Settings):
        """Initialize the RepoCloner.

        Args:
            settings: Application settings
        """
        self.settings = settings

    def clone(self, repo_url: str) -> Path:
        """Clone a repository.

        Args:
            repo_url: GitHub repository URL

        Returns:
            Path to the cloned repository

        Raises:
            ValueError: If the URL is invalid
            subprocess.CalledProcessError: If git command fails
        """
        # Extract host name, organization/user name, and repository name from URL
        parsed_url = urlparse(repo_url)
        host = parsed_url.netloc
        path_parts = parsed_url.path.strip('/').split('/')
        if len(path_parts) < 2:
            raise ValueError(f"Invalid GitHub URL: {repo_url}")

        org_or_user = path_parts[0]
        repo_name = path_parts[1]

        # Create path for cloning
        clone_path = self.settings.repo_dir / host / org_or_user / repo_name

        # Pull if already cloned, otherwise clone
        if clone_path.exists():
            subprocess.run(["git", "-C", str(clone_path), "pull"], check=True)
        else:
            # Create directory
            clone_path.parent.mkdir(parents=True, exist_ok=True)

            # Clone repository
            subprocess.run(["git", "clone", repo_url, str(clone_path)], check=True)

        return clone_path
