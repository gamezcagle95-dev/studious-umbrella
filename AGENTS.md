# AGENTS.md - Instructions for Jules

## Coding Conventions
- Python: Use Pylint and aim for 10/10 score.
- Solidity: 0.8.26, OpenZeppelin 5.0.2.
- Date Handling: Use `datetime.datetime.now(datetime.timezone.utc)` and Zulu (`Z`) suffix.

## Verification
- Run `scripts/verify_integration.py` to ensure core protocol integrity after changes.
- Use `scripts/jules_git_controller.py` for all Git operations to ensure quality gates are respected.

## Paths
- Core contracts: `src/contracts/`
- Appraisal logic: `scripts/appraisal_engine.py`
- Integration tests: `scripts/verify_integration.py`
