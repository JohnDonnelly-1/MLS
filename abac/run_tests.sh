#!/bin/bash
# Test runner script for ABAC models
# Usage: ./run_tests.sh [options]

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname $(dirname "$SCRIPT_DIR"))"

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}ABAC Model Test Suite Runner${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Change to project root
cd "$PROJECT_ROOT"

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}ERROR: pytest is not installed${NC}"
    echo "Please install test dependencies:"
    echo "  pip install -r requirements-test.txt"
    exit 1
fi

# Default: run all tests with verbose output
if [ $# -eq 0 ]; then
    echo -e "${GREEN}Running all ABAC model tests...${NC}"
    pytest abac/test_models.py -v
    exit $?
fi

# Parse command line arguments
case "$1" in
    unit)
        echo -e "${GREEN}Running unit tests...${NC}"
        pytest abac/test_models.py -v -m unit
        ;;
    integration)
        echo -e "${GREEN}Running integration tests...${NC}"
        pytest abac/test_models.py -v -m integration
        ;;
    functional)
        echo -e "${GREEN}Running functional tests...${NC}"
        pytest abac/test_models.py -v -m functional
        ;;
    acceptance)
        echo -e "${GREEN}Running acceptance tests...${NC}"
        pytest abac/test_models.py -v -m acceptance
        ;;
    performance)
        echo -e "${YELLOW}Running performance tests (may be slow)...${NC}"
        pytest abac/test_models.py -v -m performance
        ;;
    fast)
        echo -e "${GREEN}Running fast tests (excluding performance)...${NC}"
        pytest abac/test_models.py -v -m "not slow"
        ;;
    coverage)
        echo -e "${GREEN}Running tests with coverage report...${NC}"
        pytest abac/test_models.py -v \
            --cov=abac.models \
            --cov-report=html \
            --cov-report=term-missing \
            --cov-fail-under=90
        echo ""
        echo -e "${GREEN}Coverage report generated at htmlcov/index.html${NC}"
        ;;
    parallel)
        echo -e "${GREEN}Running tests in parallel...${NC}"
        pytest abac/test_models.py -v -n auto
        ;;
    label)
        echo -e "${GREEN}Running Label model tests...${NC}"
        pytest abac/test_models.py::TestLabelModel -v
        ;;
    security)
        echo -e "${GREEN}Running Security model tests...${NC}"
        pytest abac/test_models.py::TestSecurityModel -v
        ;;
    user)
        echo -e "${GREEN}Running FakeUser model tests...${NC}"
        pytest abac/test_models.py::TestFakeUserModel -v
        ;;
    object)
        echo -e "${GREEN}Running Object model tests...${NC}"
        pytest abac/test_models.py::TestObjectModel -v
        ;;
    access)
        echo -e "${GREEN}Running access control scenario tests...${NC}"
        pytest abac/test_models.py::TestAccessControlScenarios -v
        ;;
    help)
        echo "ABAC Test Suite Runner"
        echo ""
        echo "Usage: ./run_tests.sh [option]"
        echo ""
        echo "Options:"
        echo "  (no args)    Run all tests"
        echo "  unit         Run unit tests only"
        echo "  integration  Run integration tests only"
        echo "  functional   Run functional tests only"
        echo "  acceptance   Run acceptance tests only"
        echo "  performance  Run performance tests (slow)"
        echo "  fast         Run all tests except performance"
        echo "  coverage     Run with coverage report"
        echo "  parallel     Run tests in parallel"
        echo "  label        Run Label model tests"
        echo "  security     Run Security model tests"
        echo "  user         Run FakeUser model tests"
        echo "  object       Run Object model tests"
        echo "  access       Run access control tests"
        echo "  help         Show this help message"
        echo ""
        echo "Examples:"
        echo "  ./run_tests.sh                  # Run all tests"
        echo "  ./run_tests.sh unit             # Run only unit tests"
        echo "  ./run_tests.sh coverage         # Run with coverage"
        echo "  ./run_tests.sh fast             # Skip slow tests"
        ;;
    *)
        echo -e "${RED}Unknown option: $1${NC}"
        echo "Run './run_tests.sh help' for usage information"
        exit 1
        ;;
esac

exit $?
