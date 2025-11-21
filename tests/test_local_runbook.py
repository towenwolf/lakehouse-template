"""
Test validation for Local Setup Runbook
Validates the concepts and code structure without requiring all dependencies
"""

import os
import sys
from pathlib import Path


def test_runbook_exists():
    """Test that the runbook file exists and has content"""
    runbook_path = Path(__file__).parent.parent / "docs" / "LOCAL_SETUP_RUNBOOK.md"
    assert runbook_path.exists(), "LOCAL_SETUP_RUNBOOK.md should exist"
    
    content = runbook_path.read_text()
    assert len(content) > 10000, "Runbook should have substantial content"
    print("✓ Runbook exists and has content")


def test_runbook_sections():
    """Test that runbook has all required sections"""
    runbook_path = Path(__file__).parent.parent / "docs" / "LOCAL_SETUP_RUNBOOK.md"
    content = runbook_path.read_text()
    
    required_sections = [
        "## 🎯 Overview",
        "## 📋 Prerequisites",
        "## 🏗️ Architecture Stack",
        "## 📖 Step-by-Step Setup",
        "### Step 1:",
        "### Step 2:",
        "### Step 3:",
        "DuckDB",
        "MinIO",
        "Parquet",
        "docker-compose",
        "## 🔧 Configuration and Optimization",
        "## 📊 Monitoring and Observability",
        "## 🔍 Troubleshooting",
        "## 📈 Scaling Considerations",
        "## 🧪 Testing Your Setup",
        "## 📚 Additional Resources",
    ]
    
    for section in required_sections:
        assert section in content, f"Runbook should contain section: {section}"
    
    print(f"✓ All {len(required_sections)} required sections present")


def test_runbook_mentions_free_tools():
    """Test that runbook emphasizes free and open-source tools"""
    runbook_path = Path(__file__).parent.parent / "docs" / "LOCAL_SETUP_RUNBOOK.md"
    content = runbook_path.read_text().lower()
    
    # Check for mentions of free/open-source
    assert "free" in content, "Should mention 'free'"
    assert "open" in content, "Should mention 'open' (open-source)"
    assert "local" in content, "Should mention 'local'"
    assert "no cloud" in content or "cloud-free" in content, "Should mention no cloud requirement"
    
    # Check for specific free tools
    free_tools = ["duckdb", "minio", "parquet", "prometheus", "grafana", "jupyter"]
    for tool in free_tools:
        assert tool in content, f"Should mention free tool: {tool}"
    
    print(f"✓ Runbook emphasizes free, open-source, local tools")


def test_runbook_code_examples():
    """Test that runbook has sufficient code examples"""
    runbook_path = Path(__file__).parent.parent / "docs" / "LOCAL_SETUP_RUNBOOK.md"
    content = runbook_path.read_text()
    
    # Count code blocks
    code_block_count = content.count("```")
    assert code_block_count >= 40, f"Should have at least 40 code blocks (found {code_block_count // 2} pairs)"
    
    # Check for specific code examples
    assert "docker-compose" in content, "Should have docker-compose examples"
    assert "import duckdb" in content, "Should have DuckDB Python examples"
    assert "def " in content, "Should have Python function definitions"
    assert "cat >" in content or "EOF" in content, "Should have shell script examples"
    
    print(f"✓ Runbook has {code_block_count // 2} code blocks with examples")


def test_runbook_size_constraint():
    """Test that runbook mentions the <100 GB constraint"""
    runbook_path = Path(__file__).parent.parent / "docs" / "LOCAL_SETUP_RUNBOOK.md"
    content = runbook_path.read_text()
    
    assert "100" in content and "GB" in content, "Should mention 100 GB size constraint"
    assert "small" in content.lower() or "scale" in content.lower(), "Should mention small scale"
    
    print("✓ Runbook addresses <100 GB constraint")


def test_readme_links_to_runbook():
    """Test that README.md links to the new runbook"""
    readme_path = Path(__file__).parent.parent / "README.md"
    content = readme_path.read_text()
    
    assert "LOCAL_SETUP_RUNBOOK.md" in content, "README should link to LOCAL_SETUP_RUNBOOK.md"
    assert "Local Setup" in content or "local" in content.lower(), "README should mention local setup"
    
    print("✓ README.md links to the new runbook")


def test_runbook_structure():
    """Test that runbook follows a logical structure"""
    runbook_path = Path(__file__).parent.parent / "docs" / "LOCAL_SETUP_RUNBOOK.md"
    content = runbook_path.read_text()
    lines = content.split('\n')
    
    # Check that steps are in order
    step_numbers = []
    for line in lines:
        if line.startswith("### Step "):
            try:
                step_num = int(line.split("Step ")[1].split(":")[0])
                step_numbers.append(step_num)
            except (IndexError, ValueError):
                pass
    
    assert len(step_numbers) >= 10, f"Should have at least 10 setup steps (found {len(step_numbers)})"
    
    # Check that steps are sequential
    for i in range(len(step_numbers) - 1):
        assert step_numbers[i+1] == step_numbers[i] + 1, f"Steps should be sequential: {step_numbers}"
    
    print(f"✓ Runbook has {len(step_numbers)} sequential steps")


def test_runbook_best_practices():
    """Test that runbook includes best practices"""
    runbook_path = Path(__file__).parent.parent / "docs" / "LOCAL_SETUP_RUNBOOK.md"
    content = runbook_path.read_text().lower()
    
    best_practices = [
        "security",
        "backup",
        "monitoring",
        "performance",
        "optimization",
        "troubleshooting",
    ]
    
    for practice in best_practices:
        assert practice in content, f"Should mention best practice: {practice}"
    
    print(f"✓ Runbook includes {len(best_practices)} best practices")


if __name__ == "__main__":
    print("="*70)
    print("Testing Local Setup Runbook")
    print("="*70)
    print()
    
    tests = [
        test_runbook_exists,
        test_runbook_sections,
        test_runbook_mentions_free_tools,
        test_runbook_code_examples,
        test_runbook_size_constraint,
        test_readme_links_to_runbook,
        test_runbook_structure,
        test_runbook_best_practices,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__}: Unexpected error: {e}")
            failed += 1
    
    print()
    print("="*70)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*70)
    
    if failed > 0:
        sys.exit(1)
    else:
        print("\n🎉 All tests passed!")
