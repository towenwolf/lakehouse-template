#!/bin/bash
# Template Validation Script
# This script validates that all components of the lakehouse template are properly configured

echo "=========================================="
echo "Lakehouse Template Validation"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
CHECKS_PASSED=0
CHECKS_FAILED=0

# Function to check if a file exists
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} File exists: $1"
        ((CHECKS_PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC} File missing: $1"
        ((CHECKS_FAILED++))
        return 1
    fi
}

# Function to check if a directory exists
check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} Directory exists: $1"
        ((CHECKS_PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC} Directory missing: $1"
        ((CHECKS_FAILED++))
        return 1
    fi
}

# Function to validate YAML syntax
check_yaml() {
    if command -v python3 &> /dev/null; then
        if python3 -c "import yaml; yaml.safe_load(open('$1'))" 2>/dev/null; then
            echo -e "${GREEN}✓${NC} Valid YAML: $1"
            ((CHECKS_PASSED++))
            return 0
        else
            echo -e "${RED}✗${NC} Invalid YAML: $1"
            ((CHECKS_FAILED++))
            return 1
        fi
    else
        echo -e "${YELLOW}⚠${NC} Skipping YAML validation (python3 not found): $1"
        return 0
    fi
}

# Function to validate JSON syntax
check_json() {
    if command -v python3 &> /dev/null; then
        if python3 -c "import json; json.load(open('$1'))" 2>/dev/null; then
            echo -e "${GREEN}✓${NC} Valid JSON: $1"
            ((CHECKS_PASSED++))
            return 0
        else
            echo -e "${RED}✗${NC} Invalid JSON: $1"
            ((CHECKS_FAILED++))
            return 1
        fi
    else
        echo -e "${YELLOW}⚠${NC} Skipping JSON validation (python3 not found): $1"
        return 0
    fi
}

echo "1. Checking Core Structure..."
echo "------------------------------"
check_file "README.md"
check_file ".gitignore"
check_dir "config"
check_dir "data"
check_dir "docs"
check_dir "pipelines"
echo ""

echo "2. Checking Data Layer Structure..."
echo "------------------------------------"
check_dir "data/bronze"
check_dir "data/silver"
check_dir "data/gold"
check_file "data/bronze/.gitkeep"
check_file "data/silver/.gitkeep"
check_file "data/gold/.gitkeep"
echo ""

echo "3. Checking Logging Configuration..."
echo "-------------------------------------"
check_dir "config/logging"
check_file "config/logging/README.md"
check_file "config/logging/logging.yaml"
check_yaml "config/logging/logging.yaml"
check_file "config/logging/log4j.properties"
echo ""

echo "4. Checking Monitoring Configuration..."
echo "----------------------------------------"
check_dir "config/monitoring"
check_file "config/monitoring/README.md"
check_file "config/monitoring/prometheus.yaml"
check_yaml "config/monitoring/prometheus.yaml"
check_file "config/monitoring/grafana-dashboard.json"
check_json "config/monitoring/grafana-dashboard.json"
check_file "config/monitoring/alerts.yaml"
check_yaml "config/monitoring/alerts.yaml"
echo ""

echo "5. Checking Tool Configurations..."
echo "-----------------------------------"
check_dir "config/tools"
check_file "config/tools/README.md"

# Spark
check_dir "config/tools/spark"
check_file "config/tools/spark/spark-defaults.conf"

# dbt
check_dir "config/tools/dbt"
check_file "config/tools/dbt/dbt_project.yml"
check_yaml "config/tools/dbt/dbt_project.yml"
check_file "config/tools/dbt/profiles.yml"
check_yaml "config/tools/dbt/profiles.yml"

# Airflow
check_dir "config/tools/airflow"
check_file "config/tools/airflow/airflow.cfg"
check_file "config/tools/airflow/README.md"

# Prefect
check_dir "config/tools/prefect"
check_file "config/tools/prefect/prefect.yaml"
check_yaml "config/tools/prefect/prefect.yaml"

# Dagster
check_dir "config/tools/dagster"
check_file "config/tools/dagster/dagster.yaml"
check_yaml "config/tools/dagster/dagster.yaml"
echo ""

echo "6. Checking Example Pipelines..."
echo "---------------------------------"
check_dir "pipelines/examples"
check_file "pipelines/examples/spark_pipeline.py"
check_file "pipelines/examples/airflow_dag.py"
check_file "pipelines/examples/dbt_example_model.sql"
echo ""

echo "7. Checking Documentation..."
echo "-----------------------------"
check_file "docs/ARCHITECTURE.md"
check_file "docs/GETTING_STARTED.md"
check_file "docs/TOOL_COMPARISON.md"
check_file "CONTRIBUTING.md"
echo ""

echo "8. Checking Additional Files..."
echo "--------------------------------"
check_file "config/environment-example.env"
check_file "docker-compose.example.yml"
echo ""

echo "=========================================="
echo "Validation Summary"
echo "=========================================="
echo -e "${GREEN}Checks Passed: $CHECKS_PASSED${NC}"
echo -e "${RED}Checks Failed: $CHECKS_FAILED${NC}"
echo ""

if [ $CHECKS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All validation checks passed!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Copy config/environment-example.env to .env and customize"
    echo "2. Review docs/GETTING_STARTED.md for setup instructions"
    echo "3. Choose your tool stack from docs/TOOL_COMPARISON.md"
    echo "4. Start building your lakehouse data product!"
    exit 0
else
    echo -e "${RED}✗ Some validation checks failed.${NC}"
    echo "Please fix the issues above and run this script again."
    exit 1
fi
