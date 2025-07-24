"""
CLI tools for wish-ai package.

This module provides command-line utilities for configuring and validating
the wish-ai package setup.
"""

import asyncio
import sys

from wish_core.config import get_config_manager

from .gateway import OpenAIGateway
from .gateway.base import LLMAuthenticationError, LLMConnectionError, LLMGatewayError


async def validate_openai_setup(api_key: str | None = None) -> bool:
    """Validate OpenAI API key setup.

    Args:
        api_key: Optional API key to test (defaults to environment variable)

    Returns:
        True if API key is valid and accessible
    """
    try:
        gateway = OpenAIGateway(api_key=api_key)
        is_valid = await gateway.validate_api_key()

        if is_valid:
            print("✅ OpenAI API key is valid and accessible")
            print(f"🤖 Using model: {gateway._model}")
            return True
        else:
            print("❌ OpenAI API key validation failed")
            return False

    except LLMAuthenticationError:
        print("❌ Invalid OpenAI API key")
        print("💡 Check your OPENAI_API_KEY environment variable")
        return False
    except LLMConnectionError:
        print("🌐 Network connection failed")
        print("💡 Check your internet connection and try again")
        return False
    except LLMGatewayError as e:
        print(f"❌ LLM Gateway error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def check_environment_setup() -> bool:
    """Check if the development environment is properly configured.

    Returns:
        True if environment is properly configured
    """
    print("🔍 Checking wish-ai environment setup...\n")

    config_manager = get_config_manager()
    validation_result = config_manager.validate_setup()

    # Check configuration file
    if validation_result["config_file_exists"]:
        print("✅ Configuration file found at ~/.wish/config.toml")
        if validation_result["config_file_readable"]:
            print("✅ Configuration file is readable")
        else:
            print("❌ Configuration file exists but is not readable")
    else:
        print("ℹ️  No configuration file found at ~/.wish/config.toml")

    # Check API key configuration
    if validation_result["api_key_configured"]:
        source = validation_result["api_key_source"]
        if source == "environment":
            print("✅ OpenAI API key found in environment variable")
        elif source == "config_file":
            print("✅ OpenAI API key found in configuration file")
        else:
            print("✅ OpenAI API key is configured")
    else:
        print("❌ OpenAI API key not configured")

    # Show issues if any
    if validation_result["issues"]:
        print("\n🔧 Issues found:")
        for issue in validation_result["issues"]:
            print(f"  ❌ {issue}")

        print("\n💡 To fix these issues:")
        print("  1. Get an API key from https://platform.openai.com/api-keys")
        print("  2. Set environment variable: export OPENAI_API_KEY='your-key-here'")
        print("  3. Or add to ~/.wish/config.toml:")
        print("     [llm]")
        print('     api_key = "your-key-here"')
        print("  4. Or run: wish-ai-validate --init-config")
        return False

    print("\n✅ Environment setup looks good!")
    return True


def init_config() -> bool:
    """Initialize configuration file with defaults.

    Returns:
        True if initialization was successful
    """
    try:
        config_manager = get_config_manager()
        config_manager.initialize_config()
        print(f"✅ Configuration file initialized at {config_manager.config_path}")
        print("💡 Edit the file to add your OpenAI API key:")
        print("   [llm]")
        print('   api_key = "your-openai-api-key-here"')
        return True
    except Exception as e:
        print(f"❌ Failed to initialize configuration: {e}")
        return False


def set_api_key(api_key: str) -> bool:
    """Set OpenAI API key in configuration file.

    Args:
        api_key: OpenAI API key to set

    Returns:
        True if API key was set successfully
    """
    try:
        config_manager = get_config_manager()
        config_manager.set_api_key(api_key)
        print("✅ OpenAI API key saved to configuration file")
        print("🔒 Configuration file permissions set to 600 for security")
        return True
    except Exception as e:
        print(f"❌ Failed to save API key: {e}")
        return False


def cli_main() -> None:
    """Synchronous entry point for console script."""
    asyncio.run(main())


async def main() -> None:
    """Main CLI entry point for validation tools."""
    import argparse

    parser = argparse.ArgumentParser(description="wish-ai configuration and validation tools")
    parser.add_argument("--check-env", action="store_true", help="Check environment configuration")
    parser.add_argument("--validate-api", action="store_true", help="Validate OpenAI API key")
    parser.add_argument("--init-config", action="store_true", help="Initialize configuration file with defaults")
    parser.add_argument("--set-api-key", type=str, help="Set OpenAI API key in configuration file")
    parser.add_argument("--api-key", type=str, help="Test specific API key (instead of configuration hierarchy)")

    args = parser.parse_args()

    # Handle configuration management commands
    if args.init_config:
        success = init_config()
        sys.exit(0 if success else 1)

    if args.set_api_key:
        success = set_api_key(args.set_api_key)
        sys.exit(0 if success else 1)

    # Default behavior: run validation checks
    if not any([args.check_env, args.validate_api]):
        args.check_env = True
        args.validate_api = True

    success = True

    if args.check_env:
        success &= check_environment_setup()
        if args.validate_api:
            print()  # Add spacing

    if args.validate_api:
        print("🔍 Validating OpenAI API connection...")
        success &= await validate_openai_setup(args.api_key)

    if success:
        print("\n🎉 All checks passed! wish-ai is ready to use.")
        sys.exit(0)
    else:
        print("\n❌ Some checks failed. Please fix the issues above.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
