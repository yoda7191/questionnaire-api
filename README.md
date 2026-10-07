# Questionnaire Scoring API

A small REST API that scores standardized psychological questionnaires. Clients fetch a scale, submit item answers, and get validated subscale scores back. Every submission is stored for aggregate statistics.

Built with FastAPI, SQLAlchemy 2.0, and Pydantic v2.

## Quick start

With Docker:

```bash
docker build -t questionnaire-api
docker run -p 8000:8000 questionnaire-api
```

Or locally:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open <http://localhost:8000/docs> for interactive documentation.

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Liveness check |
| GET | `/scales` | List available scales |
| GET | `/scales/{scale_id}` | One scale with it items (no scoring key) |
| POST | `/scales/{scale_id}/submissions` | Score and store answers (201) |
| GET | `/submissions/{submission_id}` | One stored submission |
| GET | `/scales/{scale_id}/stats` | n, mean, and SD per subscale |

## Examples

```bash
# List scales
curl localhost:8000/scales

# Submit answers to the 50-item Big Five scale (all answered 4 here)
curl -X POST localhost:800/scales/ipip-bfm-50/submissions \
    -H "Content-Type: application/json" \
    -d "{\"answers\": {$(for p in e a c s i; do for k in $(seq 1 10); do printf '"%s%s": 4,' $p $k; done; done | sed 's/,$//')}}"

# Aggregate statistics
curl localhost:8000/scales/ipip-bfm-50/stats
```

Invalid answers return a single 422 listing every problem:

```json
{"detail": [
    {"item": "e2", "error": "missing"},
    {"item": "x9", "error": "unknown item"},
    {"item": "a1", "error": "value 7 outsie 1-5"}
]}
```

## Design decisions

- **Subscale means, not sums.** Means keep subscales with different item counts on the same metric as the response scale.
- **Reverse scoring** uses `(min + max) - answer`, so it works for any range, not only 1–5.
- **The scoring key stays server-side.** `GET /scales/{id}` returns item ids and text only; reverse flags and subscale assignments are filtered out by the response model.
- **Two-layer validation.** Pydantic checks the request's shape (an object of strict integers, not empty). A scale-aware function then checks content against the requested scale (missing items, unknown items, out-of-range values) and reports all problems at once.
- **Strict integers.** `"4"` and `4.0` are rejected instead of silently converted, because a malformed answer usually means a client bug.
- **Scoring is pure.** `app/scoring.py` has no FastAPI or database imports, so it is unit-tested in isolation.
- **Scales are data, not code.** Each questionnaire is a JSON file in `scales/`, validated at startup. An invalid file stops the app with a clear error instead of failing at request time.
- **Raw answers are stored next to scores**, so scores can be recomputed if scoring logic ever changes. Each submission also records a hash of the scale file, and statistics only include submissions made with the current version.
- **App factory.** `create_app(settings)` builds the app, so tests run against an in-memory database and fixture scales without touching real data.

## Project structure

```text
app/
  main.py              app factory, lifespan, exception handler, /health
  config.py            settings from environment variables
  db.py                engine creation, per-request session dependency
  models.py            Submission table (SQLAlchemy)
  schemas.py           request/response models (Pydantic)
  scales.py            scale models, loader
  scoring.py           validate_answers, reverse, score
  deps.py              shared dependencies (scale lookup, session)
  routers/
    scales.py          /scales, /scales/{id}, /scales/{id}/stats
    submissions.py     POST submissions, GET /submissions/{id}
scales/                questionnaire definitions (JSON)
tests/                 unit and API tests, fixture scale
```

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite:///./data/app.db` | Where submissions are stored |
| `SCALES_DIR` | `scales` | Folder of scale JSON files |

## Tests

```bash
pytest --cov=app
ruff check . && ruff format --check .
```

29 tests, about 98% coverage. CI runs lint and tests on every push.

## Limitations

- SQLite and no migrations; tables are created at startup. Fine for one table, not for a schema that evolves.
- No authentication: anyone can submit.
- On free hosting tiers the filesystem may reset on redeploy, which wipes stored submissions.
- Statistics are aggregated in Python. At larger scale, subscale scores would go in their own table and be aggregated in SQL.

## Scale source

Items come from the International Personality Item Pool ([ipip.ori.org](https://ipip.ori.org)), which is in the public domain. `scales/ipip-bfm-50.json` contains the 50-item Big-Five Factor Markers. Scores are for demonstration only and are not norm-referenced.
