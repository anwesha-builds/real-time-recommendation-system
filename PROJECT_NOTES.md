# Project Notes

Internal working notes for the Real-Time Content Recommendation System.
This file tracks **what has been built, why, and how the pieces connect** —
updated alongside the code so it never drifts from what's actually running.
Not meant to replace the README (that's the public-facing doc); this is the
build log.

---

## 1. How the modules talk to each other

```
Client
  |
  |--- POST /event -----------------> interaction_routes.py (producer)
  |                                       |
  |                                       v
  |                                 Redis list "event_queue"
  |                                       |
  |                                       v  (background thread, started in main.py)
  |                                 event_consumer.py (consumer)
  |                                       |
  |                      +----------------+----------------+
  |                      v                                 v
  |              PostgreSQL (interaction_events)    Redis real-time state:
  |              -- permanent history --             - session_score:{user}:{session}
  |                                                   - latest_session:{user}
  |                                                   - deletes recommendations:{user} cache
  |
  |--- GET /recommendations/{user_id} -> recommendation_routes.py
                                              |
                                              v
                                    Redis cache "recommendations:{user_id}"?
                                        hit  -> return cached (fast path)
                                        miss -> recommendation_service.py
                                                   |
                                         +---------+----------+
                                         v                    v
                                 historical_scores      session_scores
                                 (Postgres, full         (Redis hash,
                                  interaction history)    live, O(1) read)
                                         |                    |
                                         +--------+-----------+
                                                  v
                                    final_score = hist*0.6 + session*0.4
                                                  |
                                                  v
                                   top genres -> query Content table
                                   -> exclude already-watched -> top 10
                                                  |
                                                  v
                                   cache in Redis (60s TTL) -> return
```

**Module responsibilities:**
- `app/database.py` — Postgres engine/session (unchanged since v1)
- `app/redis_client.py` — single shared Redis connection, used by routes, service, and consumer
- `app/constants.py` — `EVENT_WEIGHTS`, now the single source of truth (was duplicated before)
- `app/routes/interaction_routes.py` — **producer**: validates an event and pushes it to the Redis queue, returns immediately
- `app/services/event_consumer.py` — **consumer**: background thread that pops events off the queue, writes them to Postgres, and updates live Redis state (session score, latest session, cache invalidation)
- `app/services/recommendation_service.py` — scoring logic: historical score from Postgres (full history) blended with session score read from Redis (live, no DB hit)
- `app/routes/recommendation_routes.py` — HTTP layer + response cache (60s TTL)
- `app/routes/analytics_routes.py` — unchanged, still pure Postgres aggregation

---

## 2. Progress log

### Step 0 (pre-existing) — Core backend
FastAPI + PostgreSQL + SQLAlchemy. Weighted genre scoring (`historical*0.6 + session*0.4`),
all computed synchronously from Postgres on every request. Analytics endpoint. Synthetic
dataset generator (250 users / 800 content / 15k events).

### Step 1 — Redis caching on `GET /recommendations/{user_id}`
- Added `app/redis_client.py`
- Response cached per user for 60s; `"cached": true/false"` field added so the effect is visible
- Cache invalidated whenever a new event for that user arrives
- **Why:** closes the gap with the resume claim "Redis for real-time state" / "low-latency FastAPI service" — previously there was no caching at all
- **Verified:** first call `cached:false`, repeat call `cached:true`, cache busts after a new event

### Step 2 — Producer-consumer event pipeline
- `POST /event` no longer writes to Postgres directly — it pushes the validated event onto a
  Redis list (`event_queue`) and returns immediately (producer)
- A background thread (started on app startup in `main.py`) runs `consume_events()`, which
  blocks on `BLPOP`, and for each event: writes it to Postgres, then updates real-time state
- **Why:** this is the actual "producer–consumer architecture" referenced on the resume —
  previously every write was a direct, synchronous DB insert inside the request

### Step 3 — Real-time session scoring in Redis
- The consumer now maintains `session_score:{user_id}:{session_id}` (a Redis hash of
  genre -> score, updated incrementally via `HINCRBYFLOAT`) and `latest_session:{user_id}`
- `recommendation_service.py` reads the current session's score straight from Redis instead
  of re-querying Postgres for the user's latest session on every recommendation request
- **Why:** this is the "session-aware... real-time" part of the pipeline — it removes a
  full table query from the hot path and makes session state genuinely live instead of
  recomputed from history each time
- **Verified end-to-end:** posted an event -> confirmed it drained from the Redis queue ->
  confirmed `session_score` hash updated -> confirmed the row landed in Postgres -> confirmed
  `GET /recommendations` re-ranked using the new session score and cache correctly invalidated

---

## 3. What's next (not yet built)

- **Step 4 — Simple collaborative filtering:** item-item cosine similarity over the
  user-item interaction matrix (plain pandas/numpy), blended as a second signal alongside
  the existing genre-weighted score. Covers the "collaborative/content-based ranking" claim.
- **Step 5 — Polish for presentation:** update README with the real architecture diagram,
  add a handful of pytest tests (scoring function, producer, consumer), optionally a
  Dockerfile/docker-compose for a one-command demo.

---

## 4. Known trade-offs (intentional, for a project this size)

- The consumer runs as a single daemon thread in-process, not a separate service — enough
  to demonstrate the producer-consumer pattern without adding Celery/Kafka/separate deploys.
- Event processing is effectively immediate (BLPOP + fast DB write) but technically
  eventually-consistent — a `POST /event` response doesn't guarantee the row exists in
  Postgres yet, only that it's queued. Acceptable for this project's scale.
- `session_score` Redis hashes expire after 1 hour to avoid unbounded growth across sessions.
