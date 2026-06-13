# Real-Time Recommendation System

A **backend recommendation system** built using **FastAPI, PostgreSQL, and SQLAlchemy** that processes user interaction events and generates **personalized content recommendations** using **weighted scoring and session-aware ranking**.

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

Final recommendation score:

```text
(Historical Score × 0.6)
+
(Session Score × 0.4)
```

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

### Database

* PostgreSQL
* SQLAlchemy ORM

### Validation

* Pydantic

### API Documentation

* Swagger UI

---

# Project Architecture

```text
Client
   ↓
FastAPI Backend
   ↓
Pydantic Validation
   ↓
Recommendation Service
   ↓
SQLAlchemy ORM
   ↓
PostgreSQL Database
```

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

---

## Recommendations

```http
GET /recommendations/{user_id}
```

Returns personalized recommendations.

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

Configure `.env`:

```env
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/recommendation_db
```

Run server:

```bash
uvicorn app.main:app --reload
```

Open Swagger Docs:

```text
http://127.0.0.1:8000/docs
```

---

# Challenges Faced

* Designing realistic recommendation data
* Creating weighted recommendation scoring
* Implementing session-aware personalization
* Managing recommendation diversity
* Debugging PostgreSQL connection issues

---

# Future Improvements

* Redis caching
* Real-time recommendations
* Collaborative filtering
* Hybrid recommendation model
* Docker deployment
* Recommendation explainability

---

# Learning Outcomes

Through this project, I learned:

* REST API development using FastAPI
* Database schema design
* SQLAlchemy ORM
* Recommendation system fundamentals
* Session-aware personalization
* Backend analytics
* Debugging and system design
