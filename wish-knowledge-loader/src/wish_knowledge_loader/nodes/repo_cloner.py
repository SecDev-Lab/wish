"""Repository cloning functionality."""

import logging
import subprocess
from pathlib import Path
from urllib.parse import urlparse

from wish_knowledge_loader.settings import Settings
from wish_knowledge_loader.utils.logging_utils import setup_logger


class RepoCloner:
    """Class for cloning GitHub repositories."""

    def __init__(self, settings: Settings, logger: logging.Logger = None):
        """Initialize the RepoCloner.

        Args:
            settings: Application settings
            logger: Logger instance
        """
        self.settings = settings
        self.logger = logger or setup_logger("wish-knowledge-loader.repo_cloner")

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
        self.logger.info(f"Cloning repository: {repo_url}")

        # Extract host name, organization/user name, and repository name from URL
        parsed_url = urlparse(repo_url)
        host = parsed_url.netloc
        path_parts = parsed_url.path.strip('/').split('/')
        if len(path_parts) < 2:
            self.logger.error(f"Invalid GitHub URL: {repo_url}")
            raise ValueError(f"Invalid GitHub URL: {repo_url}")

        org_or_user = path_parts[0]
        repo_name = path_parts[1]
        self.logger.debug(f"Parsed URL: host={host}, org/user={org_or_user}, repo={repo_name}")

        # Create path for cloning
        clone_path = self.settings.repo_dir / host / org_or_user / repo_name
        self.logger.debug(f"Clone path: {clone_path}")

        # Pull if already cloned, otherwise clone
        if clone_path.exists():
            self.logger.info("Repository already exists, pulling latest changes")
            subprocess.run(["git", "-C", str(clone_path), "pull"], check=True)
            self.logger.info("Successfully pulled latest changes")
        else:
            # Create directory
            self.logger.debug(f"Creating directory: {clone_path.parent}")
            clone_path.parent.mkdir(parents=True, exist_ok=True)

            # Clone repository
            self.logger.info(f"Cloning repository to {clone_path}")
            subprocess.run(["git", "clone", repo_url, str(clone_path)], check=True)
            self.logger.info("Successfully cloned repository")

        return clone_path
