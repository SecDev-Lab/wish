#!/bin/bash

# Live E2E test runner for wish
# This script helps run live environment tests safely

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== wish Live E2E Test Runner ===${NC}\n"

# Check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}Checking prerequisites...${NC}"
    
    # OpenAI API key check removed - Python code handles it
    
    # Check if VPN might be connected (optional check)
    if ping -c 1 -W 2 10.10.10.3 > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Can reach HTB target (10.10.10.3)${NC}"
        export HTB_VPN_CONNECTED=true
    else
        echo -e "${YELLOW}⚠ Cannot reach HTB target${NC}"
        echo "  Make sure VPN is connected: sudo openvpn --config HTB.ovpn --daemon"
        read -p "Continue anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    echo
}

# Show menu
show_menu() {
    echo -e "${BLUE}Select test to run:${NC}"
    echo "1) Environment setup check"
    echo "2) Discovery phase test"
    echo "3) Enumeration phase test"
    echo "4) Exploitation planning test"
    echo "5) Full attack chain (15+ minutes)"
    echo "6) All tests"
    echo "0) Exit"
    echo
}

# Run selected test
run_test() {
    case $1 in
        1)
            echo -e "${BLUE}Running environment setup check...${NC}"
            uv run pytest e2e-tests/scenarios/test_htb_lame_live.py::test_live_environment_setup -v
            ;;
        2)
            echo -e "${BLUE}Running discovery phase test...${NC}"
            uv run pytest e2e-tests/scenarios/test_htb_lame_live.py::TestHTBLameLive::test_htb_lame_discovery_phase -v -s
            ;;
        3)
            echo -e "${BLUE}Running enumeration phase test...${NC}"
            uv run pytest e2e-tests/scenarios/test_htb_lame_live.py::TestHTBLameLive::test_htb_lame_enumeration_phase -v -s
            ;;
        4)
            echo -e "${BLUE}Running exploitation planning test...${NC}"
            uv run pytest e2e-tests/scenarios/test_htb_lame_live.py::TestHTBLameLive::test_htb_lame_exploitation_planning -v -s
            ;;
        5)
            echo -e "${BLUE}Running full attack chain test...${NC}"
            echo -e "${YELLOW}This will take 15+ minutes and use OpenAI API credits${NC}"
            read -p "Continue? (y/N) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                uv run pytest e2e-tests/scenarios/test_htb_lame_live.py::TestHTBLameLive::test_htb_lame_full_attack_chain -v -s --log-cli-level=INFO
            fi
            ;;
        6)
            echo -e "${BLUE}Running all live tests...${NC}"
            echo -e "${YELLOW}This will take 30+ minutes and use OpenAI API credits${NC}"
            read -p "Continue? (y/N) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                uv run pytest e2e-tests/scenarios/test_htb_lame_live.py -v -s
            fi
            ;;
        0)
            echo -e "${GREEN}Exiting...${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid option${NC}"
            ;;
    esac
}

# Main execution
main() {
    # Enable live environment
    export WISH_E2E_LIVE=true
    
    # Check prerequisites
    check_prerequisites
    
    # Interactive mode
    if [ $# -eq 0 ]; then
        while true; do
            show_menu
            read -p "Enter choice: " choice
            echo
            run_test $choice
            echo
            read -p "Press Enter to continue..."
            clear
        done
    else
        # Direct test execution
        case $1 in
            setup)
                run_test 1
                ;;
            discovery)
                run_test 2
                ;;
            enumeration)
                run_test 3
                ;;
            exploitation)
                run_test 4
                ;;
            full)
                run_test 5
                ;;
            all)
                run_test 6
                ;;
            *)
                echo -e "${RED}Unknown command: $1${NC}"
                echo "Usage: $0 [setup|discovery|enumeration|exploitation|full|all]"
                exit 1
                ;;
        esac
    fi
}

# Run main
main "$@"