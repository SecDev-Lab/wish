#!/bin/bash
# Script to run live HTB Lame demo tests

set -e

echo "=== HTB Lame Live Demo Test Runner ==="
echo

# Check if running in CI
if [ "$CI" = "true" ]; then
    echo "❌ Cannot run live tests in CI environment"
    exit 1
fi

# Check OpenAI API key
if [ -z "$OPENAI_API_KEY" ]; then
    echo "❌ OPENAI_API_KEY not set"
    echo "   Please set: export OPENAI_API_KEY='your-api-key'"
    exit 1
fi

# Check if user wants to run live tests
if [ "$1" != "--confirm" ]; then
    echo "⚠️  WARNING: This will run tests against real HTB targets!"
    echo "   Make sure you have:"
    echo "   - Valid HTB VPN connection"
    echo "   - Permission to test targets"
    echo "   - Stable internet connection"
    echo
    echo "To continue, run: $0 --confirm"
    exit 0
fi

echo "✅ Running live HTB Lame exploitation tests..."
echo

# Set environment variables
export WISH_E2E_LIVE=true
export HTB_VPN_CONNECTED=true

# Run specific test phases
echo "1️⃣ Testing environment setup..."
uv run pytest e2e-tests/scenarios/test_htb_lame_live.py::test_live_environment_setup -v -s

echo
echo "2️⃣ Testing HTB connectivity..."
uv run pytest e2e-tests/scenarios/test_htb_lame_live.py::TestHTBLameLive::test_htb_lame_discovery_phase -v -s

echo
echo "3️⃣ Running full exploitation chain..."
uv run pytest e2e-tests/scenarios/test_htb_lame_live.py::TestHTBLameLive::test_htb_lame_full_attack_chain -v -s

echo
echo "✅ Live demo tests completed!"