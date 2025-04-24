"""Unit tests for the clean_llm_response function."""


from wish_command_generation_api.nodes.command_modifier import clean_llm_response


def test_clean_llm_response_empty():
    """Test cleaning an empty response."""
    # Arrange
    response = ""

    # Act
    result = clean_llm_response(response)

    # Assert
    assert result == "{}"


def test_clean_llm_response_valid_json():
    """Test cleaning a valid JSON response."""
    # Arrange
    response = '{"command": "nmap -sV 10.10.10.40"}'

    # Act
    result = clean_llm_response(response)

    # Assert
    assert result == '{"command": "nmap -sV 10.10.10.40"}'


def test_clean_llm_response_markdown_code_block():
    """Test cleaning a response with markdown code block."""
    # Arrange
    response = '```json\n{"command": "nmap -sV 10.10.10.40"}\n```'

    # Act
    result = clean_llm_response(response)

    # Assert
    assert result == '{"command": "nmap -sV 10.10.10.40"}'


def test_clean_llm_response_markdown_code_block_with_language():
    """Test cleaning a response with markdown code block with language."""
    # Arrange
    response = '```bash\n{"command": "nmap -sV 10.10.10.40"}\n```'

    # Act
    result = clean_llm_response(response)

    # Assert
    assert result == '{"command": "nmap -sV 10.10.10.40"}'


def test_clean_llm_response_with_explanation():
    """Test cleaning a response with explanation."""
    # Arrange
    response = 'Here is the modified command:\n\n{"command": "nmap -sV 10.10.10.40"}'

    # Act
    result = clean_llm_response(response)

    # Assert
    assert result == '{"command": "nmap -sV 10.10.10.40"}'


def test_clean_llm_response_with_explanation_and_code_block():
    """Test cleaning a response with explanation and code block."""
    # Arrange
    response = 'Here is the modified command:\n\n```json\n{"command": "nmap -sV 10.10.10.40"}\n```'

    # Act
    result = clean_llm_response(response)

    # Assert
    assert result == '{"command": "nmap -sV 10.10.10.40"}'


def test_clean_llm_response_with_no_json():
    """Test cleaning a response with no JSON."""
    # Arrange
    response = 'This is not a JSON response'

    # Act
    result = clean_llm_response(response)

    # Assert
    assert result == '{}'


def test_clean_llm_response_with_nested_json():
    """Test cleaning a response with nested JSON."""
    # Arrange
    response = '{"command": "nmap -sV 10.10.10.40", "options": {"verbose": true, "ports": [80, 443]}}'

    # Act
    result = clean_llm_response(response)

    # Assert
    assert result == '{"command": "nmap -sV 10.10.10.40", "options": {"verbose": true, "ports": [80, 443]}}'


def test_clean_llm_response_with_multiline_json():
    """Test cleaning a response with multiline JSON."""
    # Arrange
    response = """
    {
        "command": "nmap -sV 10.10.10.40",
        "options": {
            "verbose": true,
            "ports": [80, 443]
        }
    }
    """

    # Act
    result = clean_llm_response(response)

    # Assert
    # Strip whitespace for comparison
    assert result.strip() == """{
        "command": "nmap -sV 10.10.10.40",
        "options": {
            "verbose": true,
            "ports": [80, 443]
        }
    }""".strip()
