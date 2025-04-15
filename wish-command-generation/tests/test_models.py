"""Tests for the models module."""


from wish_command_generation.models import GeneratedCommand, GenerateRequest, GenerateResponse


def test_generated_command():
    """Test the GeneratedCommand model."""
    # Test with required fields
    command = GeneratedCommand(
        command="ls -la",
        explanation="This command lists all files in the current directory, including hidden files."
    )
    assert command.command == "ls -la"
    assert command.explanation == "This command lists all files in the current directory, including hidden files."

    # Test serialization
    data = command.model_dump()
    assert data["command"] == "ls -la"
    assert data["explanation"] == "This command lists all files in the current directory, including hidden files."

    # Test deserialization
    command2 = GeneratedCommand.model_validate(data)
    assert command2.command == command.command
    assert command2.explanation == command.explanation


def test_generate_request():
    """Test the GenerateRequest model."""
    # Test with required fields only
    request = GenerateRequest(query="list all files in the current directory")
    assert request.query == "list all files in the current directory"
    assert request.context == {}

    # Test with context
    context = {
        "current_directory": "/home/user",
        "history": ["cd /home/user", "mkdir test"]
    }
    request = GenerateRequest(query="list all files in the current directory", context=context)
    assert request.query == "list all files in the current directory"
    assert request.context == context

    # Test serialization
    data = request.model_dump()
    assert data["query"] == "list all files in the current directory"
    assert data["context"] == context

    # Test deserialization
    request2 = GenerateRequest.model_validate(data)
    assert request2.query == request.query
    assert request2.context == request.context


def test_generate_response():
    """Test the GenerateResponse model."""
    # Test with required fields only
    command = GeneratedCommand(
        command="ls -la",
        explanation="This command lists all files in the current directory, including hidden files."
    )
    response = GenerateResponse(generated_command=command)
    assert response.generated_command == command
    assert response.error is None

    # Test with error
    response = GenerateResponse(
        generated_command=command,
        error="An error occurred"
    )
    assert response.generated_command == command
    assert response.error == "An error occurred"

    # Test serialization
    data = response.model_dump()
    assert data["generated_command"]["command"] == "ls -la"
    assert data["generated_command"]["explanation"] == (
        "This command lists all files in the current directory, including hidden files."
    )
    assert data["error"] == "An error occurred"

    # Test deserialization
    response2 = GenerateResponse.model_validate(data)
    assert response2.generated_command.command == response.generated_command.command
    assert response2.generated_command.explanation == response.generated_command.explanation
    assert response2.error == response.error
