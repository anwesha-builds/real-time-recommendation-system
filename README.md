# Real-Time Recommendation System

A **backend recommendation system** built using **FastAPI, PostgreSQL, Redis, and SQLAlchemy** that processes user interaction events through a **producer-consumer pipeline** and generates **personalized, hybrid content recommendations** combining **weighted genre scoring, real-time session state, and collaborative filtering**.

This project simulates a real-world recommendation engine for **movies, music, and video content**.

---

# Features

### Personalized Recommendations

Generate recommendations based on:

* Historical user behavior
* Interaction event weights
* Session-aware ranking
* Content preferences

---

### User Interaction Tracking

Supports interaction events such as:

* play
* pause
* skip
* like
* dislike
* watch_complete

Tracks behavior through:

```text
POST /event
```

---

### Real-Time Event Pipeline (Producer-Consumer)

`POST /event` doesn't write to the database directly. It pushes the event onto a
Redis queue (**producer**) and returns immediately. A background thread (**consumer**)
drains the queue, persists each event to PostgreSQL, and updates a live per-session
genre score in Redis — so session state is always current without re-querying the
database on every recommendation request.

---

### Redis Caching

`GET /recommendations/{user_id}` responses are cached in Redis for 60 seconds and
invalidated automatically whenever a new event for that user is processed.

---

### Session-Aware Recommendation System

The recommendation engine considers:

### Historical Preference

Long-term user behavior.

Example:

A user frequently interacting with:

```text
Horror
Documentary
Comedy
```

gets more recommendations from those genres.

---

### Current Session Intent

Recent session behavior is prioritized.

Example:

If a user is currently interacting with:

```text
Coding
Tech
Education
```

the system dynamically adjusts recommendations.

---

### Weighted Recommendation Logic

Events have different importance levels:

| Event Type     | Weight |
| -------------- | ------ |
| like           | +5     |
| watch_complete | +4     |
| play           | +2     |
| pause          | +1     |
| skip           | -3     |
| dislike        | -5     |

Genre score:

```text
(Historical Score × 0.6)
+
(Session Score × 0.4)
```

---

### Hybrid Ranking (Content-Based + Collaborative Filtering)

Candidates are first selected by genre match and rating (content-based). They're
then **re-ranked** using an item-item collaborative filtering signal: a
user-item interaction matrix is built from all events, item-item cosine
similarity is computed (pandas + scikit-learn), and each candidate's score is
boosted based on its similarity to content the user already liked:

```text
Final Score = Content Rating + (Collaborative Filtering Score × weight)
```

The similarity matrix is cached in memory and rebuilt every 10 minutes rather
than recomputed on every request.

---

### Analytics Endpoint

Provides platform analytics including:

* Most watched content
* Most liked content
* Skip rate

Endpoint:

```text
GET /analytics/top-content
```

---

# Tech Stack

### Backend

* FastAPI
* Python

### Database & Caching

* PostgreSQL
* SQLAlchemy ORM
* Redis (real-time state, caching, event queue)

### Recommendation Logic

* Pandas / NumPy (interaction matrix)
* scikit-learn (item-item cosine similarity)

### Validation

* Pydantic

### Testing

* Pytest

### API Documentation

* Swagger UI

---

# Project Architecture

```text
Client
   |
   |-- POST /event ------------> FastAPI (producer)
   |                                 |
   |                                 v
   |                        Redis queue "event_queue"
   |                                 |
   |                                 v   (background thread)
   |                        Event Consumer
   |                          |            |
   |                          v            v
   |                    PostgreSQL    Redis real-time state
   |                  (interaction     (session score,
   |                     history)       cache invalidation)
   |
   |-- GET /recommendations/{user_id} --> FastAPI
                                             |
                                             v
                                   Redis cache (60s)? -- hit --> return
                                             |
                                            miss
                                             v
                                   Recommendation Service
                                    - historical score (PostgreSQL)
                                    - session score (Redis, live)
                                    - collaborative filtering
                                      re-rank (pandas + scikit-learn)
                                             |
                                             v
                                   Top 10 recommendations
```

See [`PROJECT_NOTES.md`](PROJECT_NOTES.md) for the detailed build log and
module-by-module breakdown.

---

# Database Schema

### Users

Stores user information.

Fields:

```text
id
name
email
created_at
```

---

### Content

Stores recommendation content.

Fields:

```text
id
title
genre
tags
duration
language
rating
content_type
```

Content Types:

* movie
* music
* video

---

### Interaction Events

Stores user activity.

Fields:

```text
id
user_id
content_id
event_type
timestamp
session_id
```

---

# Synthetic Dataset

Generated realistic recommendation-system data:

* 250 users
* 800 content items
* 15,000 interaction events

Includes:

* Persona-driven user behavior
* Genre preferences
* Realistic timestamps
* Session patterns

---

# API Endpoints

## Home

```http
GET /
```

---

## Event Tracking

```http
POST /event
```

Example request:

```json
{
  "user_id": 10,
  "content_id": 20,
  "event_type": "like",
  "session_id": "session_101"
}
```

The event is pushed to a Redis queue and processed asynchronously by the
background consumer — the response confirms it was **queued**, not that it's
written to PostgreSQL yet (that happens within milliseconds via the consumer).

---

## Recommendations

```http
GET /recommendations/{user_id}
```

Returns personalized recommendations, blending historical + live session
genre scoring with a collaborative-filtering re-rank. Response includes a
`cached` flag indicating whether it was served from the 60s Redis cache.

---
<img src="screenshots/recommendation_API_output.png" width="800">

## Analytics

```http
GET /analytics/top-content
```

Returns:

* Most watched content
* Most liked content
* Skip rate

---
<img src="screenshots/analytics_output.png" width="800">

# Installation

Clone repository:

```bash
git clone <https://github.com/anwesha-builds/real-time-recommendation-system>
```

Move into project folder:

```bash
cd real-time-recommendation-system
```

Create virtual environment:

```bash
python -m venv venv
```

Activate virtual environment:

### Windows

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Make sure Redis is installed and running locally (e.g. `redis-server`, or via
Docker: `docker run -p 6379:6379 redis`).

Configure `.env` (see `.env.example`):

```env
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/recommendation_db
REDIS_URL=redis://localhost:6379/0
```

Run server:

```bash
uvicorn app.main:app --reload
```

Open Swagger Docs:

```text
http://127.0.0.1:8000/docs
```

Run tests:

```bash
pytest
```

---

# Challenges Faced

* Designing realistic recommendation data
* Creating weighted recommendation scoring
* Implementing session-aware personalization
* Managing recommendation diversity
* Debugging PostgreSQL connection issues
* Keeping a background consumer thread and the request thread safely sharing
  one Redis connection
* Deciding how much to blend collaborative filtering into content-based
  ranking without one signal drowning out the other
* Avoiding recomputing the full item-item similarity matrix on every request
  while keeping it reasonably fresh

---

# Future Improvements

* Docker deployment (one-command setup for Postgres + Redis + app)
* Recommendation explainability ("why this was recommended")
* Expand collaborative filtering to surface cross-genre candidates, not just
  re-rank within the genre-matched pool
* Basic auth / rate limiting on endpoints
* CI pipeline running the test suite on push

---

# Learning Outcomes

Through this project, I learned:

* REST API development using FastAPI
* Database schema design
* SQLAlchemy ORM
* Recommendation system fundamentals
* Session-aware personalization
* Backend analytics
* Producer-consumer patterns with Redis as a lightweight queue
* Caching strategies and cache invalidation
* Collaborative filtering via item-item cosine similarity (pandas + scikit-learn)
* Writing unit tests for business logic independent of a live database
* Debugging and system design
