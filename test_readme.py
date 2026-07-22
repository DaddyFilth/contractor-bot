"""
Tests for README.md.

README.md contains no executable code, so these tests verify that its
documentation stays consistent with the actual state of the repository:
referenced files exist, documented environment variables match
`.env.example`, documented HTTP endpoints exist in `main.py`, the example
`business_config.json` snippet is valid and consistent with the real
config file, and the markdown itself is structurally well-formed.

This guards against "doc drift" — README claims that silently go stale
as the code changes.
"""

import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent
README_PATH = REPO_ROOT / "README.md"
MAIN_PY_PATH = REPO_ROOT / "main.py"
ENV_EXAMPLE_PATH = REPO_ROOT / ".env.example"
BUSINESS_CONFIG_PATH = REPO_ROOT / "business_config.json"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _readme_text() -> str:
    return README_PATH.read_text(encoding="utf-8")


def _main_py_text() -> str:
    return MAIN_PY_PATH.read_text(encoding="utf-8")


def _get_section(text: str, heading: str) -> str:
    """Return the body of a level-2 (``## Heading``) markdown section,
    up to (but not including) the next level-2 heading."""
    pattern = rf"^## {re.escape(heading)}\s*$(.*?)(?=^## |\Z)"
    match = re.search(pattern, text, re.MULTILINE | re.DOTALL)
    assert match, f"Section '## {heading}' not found in README.md"
    return match.group(1)


def _extract_pipe_tables(text: str):
    """Return a list of raw markdown pipe-tables (each a list of lines)."""
    tables = []
    current = []
    for line in text.splitlines():
        if line.strip().startswith("|"):
            current.append(line)
        else:
            if current:
                tables.append(current)
                current = []
    if current:
        tables.append(current)
    return tables


def _parse_table(table_lines):
    """Parse a raw pipe-table into a list of rows (each a list of cell
    strings). Skips the header/body separator row (e.g. ``|---|---|``)."""
    rows = []
    for i, line in enumerate(table_lines):
        stripped = line.strip()
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if i == 1 and all(re.fullmatch(r":?-+:?", c) for c in cells):
            continue
        rows.append(cells)
    return rows


def _env_example_vars() -> set:
    names = set()
    for line in ENV_EXAMPLE_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        names.add(line.split("=", 1)[0].strip())
    return names


# ---------------------------------------------------------------------------
# Basic sanity
# ---------------------------------------------------------------------------


def test_readme_exists_and_is_non_empty():
    assert README_PATH.is_file()
    content = _readme_text()
    assert len(content.strip()) > 0


def test_readme_starts_with_title():
    first_line = _readme_text().splitlines()[0]
    assert first_line.startswith("# "), "README should start with an H1 title"


@pytest.mark.parametrize(
    "heading",
    [
        "What It Does",
        "Stack",
        "Repository Structure",
        "Local Development",
        "Environment Variables",
        "Deployment",
        "Lead Source Webhooks",
        "Business Configuration",
    ],
)
def test_required_top_level_sections_present(heading):
    content = _readme_text()
    assert re.search(rf"^## {re.escape(heading)}\s*$", content, re.MULTILINE), (
        f"Expected top-level section '## {heading}' in README.md"
    )


# ---------------------------------------------------------------------------
# Markdown table structural integrity
# ---------------------------------------------------------------------------


def test_all_pipe_tables_have_consistent_column_counts():
    tables = _extract_pipe_tables(_readme_text())
    assert len(tables) >= 6, "Expected at least 6 pipe tables in README.md"
    for table_lines in tables:
        rows = _parse_table(table_lines)
        assert rows, f"Table produced no rows: {table_lines[:1]}"
        header_len = len(rows[0])
        for row in rows:
            assert len(row) == header_len, (
                f"Row {row!r} has {len(row)} columns, "
                f"expected {header_len} to match header {rows[0]!r}"
            )


def test_all_pipe_tables_have_a_separator_row():
    tables = _extract_pipe_tables(_readme_text())
    for table_lines in tables:
        assert len(table_lines) >= 2, "Table must have a header and separator row"
        separator_cells = [
            c.strip() for c in table_lines[1].strip().strip("|").split("|")
        ]
        assert all(re.fullmatch(r":?-+:?", c) for c in separator_cells), (
            f"Second row of table is not a valid markdown separator: {table_lines[1]!r}"
        )


# ---------------------------------------------------------------------------
# Repository Structure table -> files actually exist
# ---------------------------------------------------------------------------


def test_repository_structure_table_references_existing_files():
    section = _get_section(_readme_text(), "Repository Structure")
    referenced = re.findall(r"`([^`]+)`", section)
    assert referenced, "Expected backtick-quoted filenames in Repository Structure table"

    checked_any = False
    for entry in referenced:
        # Entries may look like ".env" / ".env.example" but only the
        # backtick spans themselves are captured individually, so each
        # entry is a single filename/token.
        candidate = REPO_ROOT / entry
        if entry in (".env",):
            # .env is intentionally git-ignored and won't exist in a
            # fresh checkout; skip it.
            continue
        assert candidate.is_file(), f"README references '{entry}' but it does not exist in the repo"
        checked_any = True

    assert checked_any, "No verifiable file references were found in Repository Structure table"


def test_repository_structure_table_lists_expected_files():
    section = _get_section(_readme_text(), "Repository Structure")
    referenced = set(re.findall(r"`([^`]+)`", section))
    expected = {
        "main.py",
        "business_config.json",
        ".env.example",
        "supabase_schema.sql",
        "requirements.txt",
        "test_webhook.py",
    }
    missing = expected - referenced
    assert not missing, f"Repository Structure table is missing entries: {missing}"


# ---------------------------------------------------------------------------
# Environment Variables table <-> .env.example consistency
# ---------------------------------------------------------------------------


def test_environment_variables_table_matches_env_example():
    section = _get_section(_readme_text(), "Environment Variables")
    documented = set(re.findall(r"`([A-Z][A-Z0-9_]*)`", section))
    actual = _env_example_vars()

    assert documented, "No environment variables found in README's Environment Variables table"
    assert actual, ".env.example appears to define no variables"

    missing_from_readme = actual - documented
    missing_from_env_example = documented - actual

    assert not missing_from_readme, (
        f"Variables in .env.example not documented in README: {missing_from_readme}"
    )
    assert not missing_from_env_example, (
        f"Variables documented in README but absent from .env.example: {missing_from_env_example}"
    )


def test_webhook_secret_length_requirement_is_consistent():
    # Regression/consistency check: the "min 32 chars" guidance should be
    # stated the same way in both README and .env.example so operators
    # don't get conflicting instructions.
    readme_section = _get_section(_readme_text(), "Environment Variables")
    env_example_text = ENV_EXAMPLE_PATH.read_text(encoding="utf-8")

    assert "min 32 chars" in readme_section
    assert "min 32 chars" in env_example_text


# ---------------------------------------------------------------------------
# Documented HTTP endpoints actually exist in main.py
# ---------------------------------------------------------------------------


def test_lead_source_webhook_endpoints_exist_in_main():
    section = _get_section(_readme_text(), "Lead Source Webhooks")
    rows = _parse_table(_extract_pipe_tables(section)[0])
    header, *body_rows = rows
    assert header == ["Source", "Endpoint"]

    main_source = _main_py_text()
    for _source, endpoint_cell in body_rows:
        match = re.search(r"`(POST|GET)\s+(/\S+)`", endpoint_cell)
        assert match, f"Could not parse endpoint from cell: {endpoint_cell!r}"
        method, path = match.group(1), match.group(2)

        literal_decorator = f'@app.{method.lower()}("{path}")'
        if literal_decorator in main_source:
            continue

        # Dynamic routes such as /webhook/{source_type} cover the
        # remaining concrete paths (e.g. /webhook/generic).
        dynamic_decorator = f'@app.{method.lower()}("/webhook/{{source_type}}")'
        assert path.startswith("/webhook/") and dynamic_decorator in main_source, (
            f"README documents endpoint '{method} {path}' but no matching "
            f"route was found in main.py"
        )


def test_twilio_webhook_urls_reference_endpoints_defined_in_main():
    section = _get_section(_readme_text(), "Deployment")
    urls = re.findall(r"`https://your-app\.onrender\.com(/\S+)`", section)
    assert urls, "Expected onrender.com example URLs in the Twilio webhooks section"

    main_source = _main_py_text()
    for path in urls:
        assert f'@app.post("{path}")' in main_source or f'@app.get("{path}")' in main_source, (
            f"README documents Twilio webhook path '{path}' but it has no "
            f"corresponding route in main.py"
        )


def test_followup_cron_endpoint_exists_in_main():
    section = _get_section(_readme_text(), "Deployment")
    match = re.search(r"\*\*URL:\*\*\s*`https://your-app\.onrender\.com(/\S+)`", section)
    assert match, "Could not find the follow-up cron job URL in README"
    path = match.group(1)

    method_match = re.search(r"\*\*Method:\*\*\s*(GET|POST)", section)
    assert method_match, "Could not find the follow-up cron job HTTP method in README"
    method = method_match.group(1).lower()

    assert f'@app.{method}("{path}")' in _main_py_text(), (
        f"README documents follow-up cron endpoint '{method.upper()} {path}' "
        f"but no matching route exists in main.py"
    )


# ---------------------------------------------------------------------------
# Business Configuration example snippet
# ---------------------------------------------------------------------------


def test_business_configuration_example_is_valid_json():
    section = _get_section(_readme_text(), "Business Configuration")
    match = re.search(r"```json\s*(\{.*?\})\s*```", section, re.DOTALL)
    assert match, "Expected a fenced ```json code block in Business Configuration section"

    parsed = json.loads(match.group(1))
    assert isinstance(parsed, dict)
    assert parsed  # non-empty


def test_business_configuration_example_keys_are_subset_of_real_config():
    section = _get_section(_readme_text(), "Business Configuration")
    match = re.search(r"```json\s*(\{.*?\})\s*```", section, re.DOTALL)
    documented_keys = set(json.loads(match.group(1)).keys())

    real_config = json.loads(BUSINESS_CONFIG_PATH.read_text(encoding="utf-8"))
    real_keys = set(real_config.keys())

    missing = documented_keys - real_keys
    assert not missing, (
        f"Business Configuration example documents keys not present in "
        f"business_config.json: {missing}"
    )


# ---------------------------------------------------------------------------
# Links
# ---------------------------------------------------------------------------


def test_all_markdown_links_use_https():
    links = re.findall(r"\[[^\]]+\]\((https?://[^)]+)\)", _readme_text())
    assert links, "Expected at least one markdown link in README.md"
    non_https = [url for url in links if not url.startswith("https://")]
    assert not non_https, f"README contains non-HTTPS links: {non_https}"


# ---------------------------------------------------------------------------
# Local Development instructions reference existing tooling
# ---------------------------------------------------------------------------


def test_local_development_commands_reference_existing_flags():
    section = _get_section(_readme_text(), "Local Development")
    documented_flags = set(re.findall(r"`(--[a-z-]+)`", section))
    assert documented_flags, "Expected documented CLI flags in Local Development section"

    test_webhook_source = (REPO_ROOT / "test_webhook.py").read_text(encoding="utf-8")
    for flag in documented_flags:
        assert flag in test_webhook_source, (
            f"README documents flag '{flag}' for test_webhook.py, but it is "
            f"not defined there"
        )


def test_local_development_run_command_references_main_app():
    section = _get_section(_readme_text(), "Local Development")
    assert "main:app" in section
    assert "main:app" in _main_py_text() or "app = FastAPI" in _main_py_text()