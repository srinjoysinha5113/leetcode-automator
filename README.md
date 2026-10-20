# NeetCode 150 Automated LeetCode Solver

An autonomous, robust, Windows-compatible Python system that processes the **NeetCode 150** problem list using a local **Llama 3.2 (3B)** model via Ollama, validates and runs test cases in an isolated subprocess environment, repairs failing solutions iteratively, verifies LeetCode account identity through persistent Playwright browser automation, and tracks all progress in a persistent state database.

---

## Key Features

1. **Local LLM Intelligence via Ollama**:
   - Zero cloud costs, no paid API keys required.
   - Built for `llama3.2:3b` with low temperature and configurable timeouts.
   - Robust AST validation verifying syntax and class/method signatures.

2. **Isolated Subprocess Execution & Test Adapters**:
   - Executes generated solutions in an isolated subprocess with strict execution timeouts and output limits.
   - Environment sanitization: strips credentials, secrets, and environment tokens.
   - Type-aware adapters for `ListNode` (linked lists with cycle detection), `TreeNode` (binary tree BFS), and complex stateful class designs (`MinStack`, `LRUCache`, `Trie`, etc.).

3. **Iterative Diagnostics & Repair Loop**:
   - If a solution fails local tests or syntax checks, detailed diagnostics (failing inputs, expected vs actual outputs, error tracebacks) are sent back to the model.
   - Automatically repairs solutions up to `MAX_REPAIR_ATTEMPTS`.

4. **Strict Account Identity Verification**:
   - Dedicated persistent Playwright browser profile (`data/browser_profile/` excluded from Git).
   - Allows safe manual login for the initial setup—**never collects or stores LeetCode passwords**, never logs session cookies.
   - Reads authenticated username via in-page GraphQL/DOM inspection and strictly compares with `EXPECTED_LEETCODE_USERNAME`.
   - Submissions are permanently disabled if identity cannot be verified or differs from configuration.

5. **Safe Submission Engine & Verification**:
   - Monaco Editor programmatic population and UI fallback.
   - Captures terminal verdicts (`Accepted`, `Wrong Answer`, `Time Limit Exceeded`, `Runtime Error`, `Compile Error`) via LeetCode's live submission check API and DOM modals.
   - Failsafe safety defaults: `AUTO_SUBMIT=false` prevents accidental submissions until explicitly enabled.

6. **Full State Persistence & Recovery**:
   - Relational schema (SQLite default with MySQL support) tracking problems, generation attempts, test runs, submissions, and identity verifications.
   - Resumes seamlessly after interruptions without duplicate submissions or lost progress.

---

## Project Structure

```
leetcode-automator/
├── app/
│   ├── __init__.py
│   ├── config.py              # Pydantic Settings & Rotating File Loggers
│   ├── models.py              # SQLAlchemy database tables & Pydantic schemas
│   ├── database.py            # SQLite/MySQL engine, sessions & DB manager
│   ├── adapters.py            # ListNode, TreeNode, DesignClass adapters & deep_equal
│   ├── problem_source.py      # NeetCode 150 manifest loader & LeetCode GraphQL fetcher
│   ├── problem_queue.py       # State-aware problem queue & recovery logic
│   ├── llm_client.py          # Ollama client, health checks, AST validation
│   ├── solution_generator.py  # Structured generation prompt formulation
│   ├── test_runner.py         # Subprocess test runner with limits & temp cleanup
│   ├── repair_loop.py         # Diagnostic feedback & multi-turn repair loop
│   ├── account_verifier.py    # Persistent Playwright identity verifier & manual login
│   ├── submitter.py           # Monaco editor injection & verdict verification
│   ├── orchestrator.py        # End-to-end pipeline controller
│   ├── reporting.py           # Rich CLI dashboards & Markdown report exporter
│   └── cli.py                 # Click CLI commands
├── data/
│   ├── neetcode150.json       # Maintained NeetCode 150 problem manifest
│   ├── solutions/             # Verified solution source files
│   ├── reports/               # Markdown progress reports
│   ├── problems/              # Cached LeetCode GraphQL problem data
│   └── browser_profile/       # Persistent Playwright profile (Git-ignored)
├── tests/                     # 31 unit and integration tests
├── logs/                      # Rotating log files
├── .env.example               # Configuration template
├── .env                       # Local active configuration
├── .gitignore                 # Security exclusion rules
├── requirements.txt           # Python dependencies
├── pyproject.toml             # Project build & test configuration
└── main.py                    # Application entrypoint
```

---

## Configuration (`.env`)

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_MODEL` | `llama3.2:3b` | Model name installed in local Ollama |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama service endpoint |
| `OLLAMA_TEMPERATURE` | `0.2` | Generation temperature |
| `EXPECTED_LEETCODE_USERNAME` | *(Your LeetCode username)* | Must match the authenticated account |
| `DATABASE_URL` | `sqlite:///data/leetcode_automator.db` | SQLite or MySQL (`mysql+pymysql://...`) |
| `AUTO_SUBMIT` | `false` | Critical safety toggle. Keep false until verified |
| `MAX_REPAIR_ATTEMPTS` | `3` | Maximum LLM repair turns per problem |
| `MAX_SUBMISSIONS_PER_PROBLEM` | `3` | Maximum retry limit on rejected submissions |
| `SUBMISSION_TIMEOUT_SECONDS` | `120` | Timeout waiting for terminal LeetCode verdict |
| `BROWSER_HEADLESS` | `false` | Visible browser window during login and submission |
| `TEST_EXECUTION_TIMEOUT_SECONDS` | `5` | Isolated subprocess test execution timeout |

---

## Verified Browser Selectors & Page Behavior

| Element | Verified Mechanism / Selector | Fallback |
|---|---|---|
| **Account Identity** | In-page GraphQL `query { userStatus { isSignedIn username } }` | `a[href*="/profile/"]`, `[data-cy="user-avatar"]` |
| **Monaco Editor** | `window.monaco.editor.getModels()[0].setValue(code)` | Click `.monaco-editor`, select all, insert text |
| **Submit Button** | `button[data-e2e-locator="console-submit-button"]` | `button:has-text("Submit")`, `[data-cy="submit-code-btn"]` |
| **Submission Result** | Intercept `/check/` response JSON (`state == "SUCCESS"`) | `[data-e2e-locator="submission-result"]` |

---

## CLI Commands

### 1. Diagnostic & Setup
```bash
# Verify all dependencies, Ollama server, model, DB, and browser:
python main.py doctor

# Initialize tables and import the 150 NeetCode problems:
python main.py setup
```

### 2. Account Verification (Manual Login)
```bash
# Opens visible browser for one-time manual LeetCode login (complete CAPTCHA/MFA):
python main.py verify-account
```

### 3. Dry-Run Mode (Safe Testing — Never Submits)
```bash
# Test first queued problem:
python main.py dry-run --limit 1

# Test a specific problem by slug:
python main.py dry-run --slug contains-duplicate
```

### 4. Live Submission Mode (Requires AUTO_SUBMIT=true)
```bash
# Process 1 problem:
python main.py run --limit 1

# Process 10 problems:
python main.py run --limit 10

# Process all remaining problems:
python main.py run --all

# Retry a specific problem that failed or was rejected:
python main.py retry contains-duplicate
```

### 5. Status & Reports
```bash
# Show real-time summary dashboard:
python main.py status

# Generate and save a markdown report:
python main.py report
```

---

## Running the Automated Test Suite

All 31 unit and integration tests mock network endpoints and external browsers to ensure zero side effects:
```bash
pytest -v
```
