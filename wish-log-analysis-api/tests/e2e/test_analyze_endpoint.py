"""E2E tests for the /analyze endpoint.

These tests are designed to be run against a deployed API endpoint, typically
hosted in a different repository or environment than the local development setup.
The tests require environment variables (API_ENDPOINT and API_KEY) to be set in
the .env.test file or in the environment where the tests are run.

When running `make e2e` from the parent repository, these tests will be executed
against the remote API endpoint specified in the environment variables.
"""

import json
import os

import pytest
import requests
from dotenv import load_dotenv
from wish_models.test_factories.command_result_factory import CommandResultSuccessFactory


def test_analyze_endpoint_success():
    """Test the /analyze endpoint with a successful command result.

    This test sends a request to the deployed API endpoint and verifies
    that it returns a 200 OK response with the expected structure.
    """
    # Load environment variables
    load_dotenv()

    # Check environment variables
    api_endpoint = os.environ.get("API_ENDPOINT")
    api_key = os.environ.get("API_KEY")

    missing_vars = []
    if not api_endpoint:
        missing_vars.append("API_ENDPOINT")
    if not api_key:
        missing_vars.append("API_KEY")

    if missing_vars:
        pytest.skip(f"Required environment variables are not set: {', '.join(missing_vars)}")

    # Create test data
    command_result = CommandResultSuccessFactory.build()

    # Send request
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key
    }

    payload = {
        "command_result": command_result.model_dump()
    }

    try:
        response = requests.post(
            f"{api_endpoint}/analyze",
            headers=headers,
            json=payload,
            timeout=30
        )

        # Display error response details
        if response.status_code != 200:
            print("\n===== Error Response =====")
            print(f"Status code: {response.status_code}")
            print(f"Response headers: {response.headers}")
            try:
                error_json = response.json()
                print(f"Response body (JSON): {json.dumps(error_json, indent=2, ensure_ascii=False)}")
            except ValueError:
                print(f"Response body (text): {response.text}")
            print("==========================\n")

        # Validate response
        assert response.status_code == 200, f"API returned a status code other than 200: {response.status_code}"

        try:
            response_data = response.json()
        except ValueError as e:
            pytest.fail(f"Response is not JSON: {e}\nResponse: {response.text}")

        assert "analyzed_command_result" in response_data, "Response does not contain 'analyzed_command_result'"
        assert response_data.get("error") is None, f"Error was returned: {response_data.get('error')}"

        analyzed_result = response_data["analyzed_command_result"]
        assert analyzed_result["num"] == command_result.num, (
            f"num does not match: expected={command_result.num}, actual={analyzed_result['num']}"
        )
        assert analyzed_result["command"] == command_result.command, (
            f"command does not match: expected={command_result.command}, "
            f"actual={analyzed_result['command']}"
        )
        assert "log_summary" in analyzed_result, "Response does not contain 'log_summary'"
        assert "state" in analyzed_result, "Response does not contain 'state'"

    except requests.RequestException as e:
        pytest.fail(f"Error occurred during API request: {e}")
