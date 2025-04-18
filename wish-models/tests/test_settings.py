"""Tests for Settings class."""

import os
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest
from wish_models.settings import Settings


class TestSettings:
    """Tests for Settings class."""

    def test_default_settings(self):
        """Test default settings initialization."""
        settings = Settings()
        # WISH_HOME might be expanded or not depending on environment
        # Just check that it contains .wish at the end
        assert str(settings.WISH_HOME).endswith(".wish")
        assert settings.OPENAI_MODEL == "gpt-4o"
        assert settings.EMBEDDING_MODEL == "text-embedding-3-small"

    def test_env_file_from_path(self):
        """Test loading settings from env file specified as Path."""
        # Create temporary env file
        with NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("OPENAI_MODEL=gpt-3.5-turbo\n")
            f.write("EMBEDDING_MODEL=text-embedding-ada-002\n")
            env_path = Path(f.name)

        try:
            # Load settings from env file
            settings = Settings(env_file=env_path)
            assert settings.OPENAI_MODEL == "gpt-3.5-turbo"
            assert settings.EMBEDDING_MODEL == "text-embedding-ada-002"
        finally:
            # Clean up
            os.unlink(env_path)

    def test_env_file_from_env_var(self):
        """Test loading settings from env file specified in environment variable."""
        # Create temporary env file
        with NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("OPENAI_MODEL=gpt-4-turbo\n")
            env_path = f.name

        try:
            # Set environment variable
            os.environ["WISH_ENV_FILE"] = env_path
            
            # Load settings
            settings = Settings()
            assert settings.OPENAI_MODEL == "gpt-4-turbo"
            
            # Clean up environment
            del os.environ["WISH_ENV_FILE"]
        finally:
            # Clean up
            os.unlink(env_path)

    def test_environment_variables_override(self):
        """Test that environment variables override env file settings."""
        # Create temporary env file
        with NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("OPENAI_MODEL=gpt-3.5-turbo\n")
            env_path = Path(f.name)

        try:
            # Set environment variable
            os.environ["OPENAI_MODEL"] = "gpt-4-vision"
            
            # Load settings
            settings = Settings(env_file=env_path)
            
            # Environment variable should override env file
            assert settings.OPENAI_MODEL == "gpt-4-vision"
            
            # Clean up environment
            del os.environ["OPENAI_MODEL"]
        finally:
            # Clean up
            os.unlink(env_path)

    def test_constructor_override(self):
        """Test that constructor parameters override environment variables and env file."""
        # Set environment variable
        os.environ["OPENAI_MODEL"] = "gpt-4-vision"
        
        # Load settings with constructor override
        settings = Settings(OPENAI_MODEL="gpt-4o-mini")
        
        # Constructor parameter should override environment variable
        assert settings.OPENAI_MODEL == "gpt-4o-mini"
        
        # Clean up environment
        del os.environ["OPENAI_MODEL"]

    def test_wish_home_path_conversion(self):
        """Test that WISH_HOME is converted to Path."""
        # Test with string
        settings = Settings(WISH_HOME="/tmp/wish")
        assert isinstance(settings.WISH_HOME, Path)
        assert settings.WISH_HOME == Path("/tmp/wish")
        
        # Test with tilde expansion
        settings = Settings(WISH_HOME="~/wish")
        assert isinstance(settings.WISH_HOME, Path)
        # The path might be expanded or not depending on environment
        # Just check that it contains 'wish' at the end
        assert str(settings.WISH_HOME).endswith("wish")

    def test_knowledge_properties(self):
        """Test knowledge directory properties."""
        settings = Settings(WISH_HOME="/tmp/wish-test")
        assert settings.knowledge_dir == Path("/tmp/wish-test/knowledge")
        assert settings.repo_dir == Path("/tmp/wish-test/knowledge/repo")
        assert settings.db_dir == Path("/tmp/wish-test/knowledge/db")
        assert settings.meta_path == Path("/tmp/wish-test/knowledge/meta.json")
