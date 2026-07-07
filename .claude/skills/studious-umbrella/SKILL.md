```markdown
# studious-umbrella Development Patterns

> Auto-generated skill from repository analysis

## Overview

This skill teaches the core development patterns, coding conventions, and automation workflows used in the `studious-umbrella` Python repository. The project focuses on smart contract integration, deployment scripting, and CI/CD automation, with a strong emphasis on consistent code style and structured commit practices. By following these guidelines, contributors can maintain code quality and streamline collaboration.

## Coding Conventions

### File Naming

- **Use camelCase** for file names.
  - Example: `deployScript.py`, `provenanceLedger.sol`

### Import Style

- **Relative imports** are preferred within the Python codebase.
  - Example:
    ```python
    from .utils import buildArtifacts
    ```

### Export Style

- **Named exports** are used for Python modules and Solidity contracts.
  - Example (Python):
    ```python
    def deploy_contract():
        pass

    __all__ = ['deploy_contract']
    ```
  - Example (Solidity):
    ```solidity
    contract ProvenanceLedger { ... }
    ```

### Commit Message Style

- **Prefixes:** Use `feat` for new features, `revert` for rollbacks.
- **Freeform messages** after the prefix.
- **Average length:** ~71 characters.
  - Example:
    ```
    feat: integrate ProvenanceLedger with ProvenanceRegistry for asset tracking
    ```

## Workflows

### smart-contract-integration-and-linkage

**Trigger:** When you need to link or unlink smart contracts and update deployment logic.  
**Command:** `/integrate-contracts`

1. **Modify contract files**:
    - Edit `src/contracts/ProvenanceLedger.sol` and/or `src/contracts/ProvenanceRegistry.sol` to add or remove integration logic.
2. **Update deployment script**:
    - Adjust `deploy.py` to reflect new linkage or remove linkage logic.
3. **Generate new build artifacts**:
    - Build contracts to create new `build-info.json` files in `artifacts/contracts/` (timestamped).
    - Update `artifacts/contracts/latest` with the latest build.
4. **(Optional) Verify ABI integration**:
    - Add or remove `scripts/verify_integration.py` for ABI verification as needed.
5. **Commit all related files together**:
    - Ensure all changes are included in a single commit.

**Example:**
```bash
# After modifying contracts and deployment logic
python deploy.py
# (Re)generate build artifacts
git add src/contracts/ProvenanceLedger.sol src/contracts/ProvenanceRegistry.sol deploy.py artifacts/contracts/* scripts/verify_integration.py
git commit -m "feat: integrate ProvenanceLedger with ProvenanceRegistry"
```

---

### add-or-update-github-actions-workflow

**Trigger:** When you want to introduce or modify a workflow for automation or code analysis in GitHub Actions.  
**Command:** `/add-github-workflow`

1. **Create or update a workflow YAML file**:
    - Place the file under `.github/workflows/` (e.g., `codeql.yml`, `summary.yml`, `stale.yml`).
2. **Commit the workflow file**:
    - Use a descriptive commit message.

**Example:**
```yaml
# .github/workflows/codeql.yml
name: "CodeQL Analysis"
on: [push, pull_request]
jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: github/codeql-action/init@v2
      - uses: github/codeql-action/analyze@v2
```
```bash
git add .github/workflows/codeql.yml
git commit -m "feat: add CodeQL workflow for static analysis"
```

## Testing Patterns

- **Test files** use the pattern `*.test.*` (e.g., `ledger.test.py`).
- **Testing framework** is not explicitly defined; check test files for conventions.
- **Best practice:** Place tests alongside or near the code they validate, using clear and descriptive test names.

**Example:**
```python
# ledger.test.py
from .ledger import ProvenanceLedger

def test_ledger_initialization():
    ledger = ProvenanceLedger()
    assert ledger.is_initialized()
```

## Commands

| Command                | Purpose                                                        |
|------------------------|----------------------------------------------------------------|
| /integrate-contracts   | Integrate or unlink smart contracts and update deployment logic |
| /add-github-workflow   | Add or update a GitHub Actions workflow                        |
```
