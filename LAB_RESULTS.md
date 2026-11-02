# Codex lab results

## Codebase inspection

The application is a FastAPI task tracker backed by a JSON file.
`app/main.py` defines routes, `app/schemas.py` validates request and response
models, `app/service.py` contains business logic, and `app/store.py` reads and
writes `data/tasks.json`. GET /tasks passes status and q from the route to
`list_tasks`, which loads the records, filters them, and returns the response.

## Reproduction and fixes

- Before the fix, GET /tasks returned four tasks but status=open returned an
  empty list. The service compared each status to the literal string "status".
  It now compares to the supplied status value.
- Before the fix, POST /tasks/1/complete returned done, but GET /tasks/1 still
  returned open with a null completed_at. Completion now updates the record
  in the loaded list and saves the list before returning it.
- The route already accepted q but the service ignored it. Search now uses
  casefold for case-insensitive substring matching separately across title
  and description, after applying the status filter. Omitting q keeps the
  existing list behavior.

## Setup and verification

Commands used on Windows (virtual-environment executables avoid shell activation):

```powershell
python -m venv .venv
# The sandbox's default temp directory caused ensurepip to fail initially.
# After selecting a writable temporary directory:
.\.venv\Scripts\python.exe -m ensurepip --upgrade --default-pip
.\.venv\Scripts\python.exe -m pip install --no-cache-dir -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m pip check
git diff --check
```

All six regression tests passed. They use isolated temporary JSON storage.
Dependency checks and whitespace checks passed.

Live curl verification passed against a fresh server on port 18000:

| Request | Verified result |
| --- | --- |
| GET /tasks | IDs 1, 2, 3, 4 |
| GET /tasks?status=open | IDs 1, 3, 4 |
| GET /tasks?status=done | ID 2 |
| GET /tasks?q=launch | ID 1 |
| GET /tasks?q=LAUNCH | ID 1 |
| GET /tasks?q=report | ID 4 |
| GET /tasks?q=CALLBACK | ID 2; description-only match |
| GET /tasks?status=open&q=plan | ID 3 |
| GET /tasks?status=done&q=plan | Empty list before completion |
| GET /tasks?q=unmatched-query | Empty list |
| POST /tasks/3/complete | done with non-null completed_at |
| GET /tasks/3 | Same completed record |
| GET /tasks/3 after server restart | Same completed record |
| GET /tasks?status=done after completion | IDs 2, 3 |
| GET /tasks?status=open&q=plan after completion | Empty list |
| GET /docs | HTTP 200 |

The runtime data was restored after verification. The final changes contain
only the service fix, regression tests, and these notes. Publishing to the
learner's GitHub account requires authenticated GitHub access.
