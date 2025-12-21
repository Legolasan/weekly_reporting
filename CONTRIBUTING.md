# Contributing to Work Tracker

Thank you for contributing to Work Tracker! This document outlines our testing requirements and guidelines.

## Testing Requirements

**All code changes must include appropriate tests.** This is strictly enforced through CI/CD.

### Coverage Requirements

- **Minimum coverage: 70%** - PRs that drop coverage below this threshold will be blocked
- **New files: 80%+** - New functionality should have comprehensive test coverage
- Coverage is automatically checked on every PR and push to main

### What Requires Tests

| Change Type | Test Requirement |
|-------------|------------------|
| Bug fix | Regression test that fails without the fix |
| New feature | Tests covering the new functionality |
| API endpoint | Integration test for the endpoint |
| Database change | Tests for CRUD operations |
| Authentication | Security-related test cases |

## Running Tests Locally

```bash
# Navigate to project directory
cd work-tracker

# Activate virtual environment
source venv/bin/activate

# Run all tests
DATABASE_URL=sqlite:///./test.db pytest tests/ -v

# Run with coverage report
DATABASE_URL=sqlite:///./test.db pytest tests/ --cov=app --cov-report=term-missing

# Run with coverage enforcement (same as CI)
DATABASE_URL=sqlite:///./test.db pytest tests/ --cov=app --cov-fail-under=70

# Run specific test file
DATABASE_URL=sqlite:///./test.db pytest tests/test_auth.py -v

# Run tests by marker
DATABASE_URL=sqlite:///./test.db pytest -m auth -v
```

## Writing Tests

### Test File Structure

```
tests/
├── conftest.py          # Shared fixtures
├── test_auth.py         # Authentication tests
├── test_dashboard.py    # Dashboard tests
├── test_input.py        # Work item input tests
├── test_analytics.py    # Analytics tests
├── test_reports.py      # Reports/export tests
└── test_admin.py        # Admin functionality tests
```

### Test Markers

Use markers to categorize tests:

```python
@pytest.mark.auth
def test_login_success():
    ...

@pytest.mark.input
def test_create_work_item():
    ...
```

Available markers: `auth`, `dashboard`, `input`, `analytics`, `reports`, `admin`

### Example: Bug Fix Test

```python
@pytest.mark.regression
def test_bug_fix_issue_123(authenticated_client, sample_work_week):
    """
    Regression test for issue #123: Empty completion_points caused error.
    
    This test ensures that submitting a form with empty completion_points
    field is handled gracefully instead of raising a validation error.
    """
    response = authenticated_client.post(
        "/api/work-items",
        data={
            "week_id": str(sample_work_week.id),
            "title": "Test Task",
            "type": "PLANNED",
            "status": "TODO",
            "assigned_points": "20",
            "completion_points": "",  # Empty - this was the bug
            "start_date": sample_work_week.week_start.isoformat(),
            "end_date": sample_work_week.week_end.isoformat(),
        },
        follow_redirects=False
    )
    # Should not return 400 validation error
    assert response.status_code in [200, 302, 303]
```

### Example: New Feature Test

```python
@pytest.mark.input
class TestNewFeature:
    """Tests for the new XYZ feature."""
    
    def test_feature_basic_functionality(self, authenticated_client):
        """Test the basic happy path."""
        ...
    
    def test_feature_edge_case(self, authenticated_client):
        """Test edge case: empty input."""
        ...
    
    def test_feature_error_handling(self, authenticated_client):
        """Test that errors are handled gracefully."""
        ...
```

## Pre-commit Hooks

We use pre-commit hooks to catch issues early:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

The hooks will:
1. Check code formatting (black)
2. Run linting (flake8)
3. Run tests on push (pytest)
4. Check coverage on push (70% minimum)

## CI/CD Pipeline

Every PR triggers:
1. **Test job**: Runs all tests with coverage enforcement
2. **Allure report**: Generates detailed test reports

PRs are blocked if:
- Any test fails
- Coverage drops below 70%

## Getting Help

- Check existing tests in `tests/` for examples
- Look at `tests/conftest.py` for available fixtures
- Run `pytest --markers` to see all available markers
