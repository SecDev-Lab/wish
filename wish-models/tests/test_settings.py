"""Tests for Settings class."""

import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from wish_models.settings import Settings, get_default_env_path


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
            # Check if OPENAI_MODEL is set in environment
            openai_model_env = os.environ.get("OPENAI_MODEL")

            # Load settings from env file
            settings = Settings(env_file=env_path)

            # If OPENAI_MODEL is set in environment, it should override env file
            if openai_model_env:
                assert settings.OPENAI_MODEL == openai_model_env
            else:
                assert settings.OPENAI_MODEL == "gpt-3.5-turbo"

            # EMBEDDING_MODEL should be from env file if not set in environment
            if "EMBEDDING_MODEL" not in os.environ:
                assert settings.EMBEDDING_MODEL == "text-embedding-ada-002"
        finally:
            # Clean up
            os.unlink(env_path)

    def test_nonexistent_env_file(self):
        """Test that nonexistent env file is ignored."""
        # Create a path to a nonexistent file
        env_path = Path("/tmp/nonexistent-env-file-for-testing")

        # Make sure the file doesn't exist
        if env_path.exists():
            os.unlink(env_path)

        # Load settings with nonexistent env file
        settings = Settings(env_file=env_path)

        # Default values should be used
        assert settings.OPENAI_MODEL == "gpt-4o"

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

    def test_get_default_env_path(self):
        """Test get_default_env_path function."""
        # Test with default WISH_HOME
        default_path = get_default_env_path()
        assert str(default_path).endswith(".wish/env")

        # Test with custom WISH_HOME
        try:
            os.environ["WISH_HOME"] = "/tmp/custom-wish-home"
            custom_path = get_default_env_path()
            assert custom_path == Path("/tmp/custom-wish-home/env")
        finally:
            # Clean up environment
            del os.environ["WISH_HOME"]
