"""
seed_data.py
------------
Populates the recommendation_db with synthetic but realistic data:
  - 250 users
  - 800 content items  (30% movies, 30% music, 40% videos)
  - 40,000 interaction events (persona-driven, not random)

Run:
    python seed_data.py
"""

import random
import sys
from datetime import datetime, timedelta

from dotenv import load_dotenv

load_dotenv()

from app.database import SessionLocal
from app.models.user import User
from app.models.content import Content
from app.models.interaction import InteractionEvent


# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────
NUM_USERS        = 250
NUM_CONTENT      = 800
NUM_INTERACTIONS = 40_000
BATCH_SIZE       = 1_000   # rows flushed per batch

random.seed(42)


# ──────────────────────────────────────────────
# CONTENT TEMPLATES
# Each entry: (title_prefix, genre, tags, duration_range_minutes, language)
# ──────────────────────────────────────────────

MOVIE_ENTRIES = [
    ("Interstellar Echoes",    "Sci-Fi",      "space,future,adventure",       (90,  160), "English"),
    ("Quantum Paradox",        "Sci-Fi",      "science,thriller,aliens",      (100, 150), "English"),
    ("Neon Horizon",           "Sci-Fi",      "cyberpunk,dystopia,tech",      (95,  145), "English"),
    ("Midnight Shadows",       "Horror",      "ghost,supernatural,dark",      (80,  120), "English"),
    ("The Haunting of Room 9", "Horror",      "paranormal,mystery,fear",      (85,  115), "English"),
    ("Blood Moon Rising",      "Horror",      "vampire,thriller,night",       (90,  130), "English"),
    ("Silent Conspiracy",      "Thriller",    "crime,suspense,detective",     (100, 150), "English"),
    ("Edge of Silence",        "Thriller",    "spy,action,government",        (110, 160), "English"),
    ("The Last Witness",       "Thriller",    "court,truth,justice",          (95,  140), "English"),
    ("Broken Mirrors",         "Drama",       "family,emotion,loss",          (100, 150), "English"),
    ("Letters to Mumbai",      "Drama",       "love,journey,india",           (110, 160), "Hindi"),
    ("The Forgotten Son",      "Drama",       "family,sacrifice,hope",        (105, 155), "English"),
    ("Laugh Factory",          "Comedy",      "funny,friends,slapstick",      (85,  110), "English"),
    ("Crazy Neighbours",       "Comedy",      "humor,family,daily-life",      (90,  120), "English"),
    ("Wrong Turn Right",       "Comedy",      "road-trip,funny,mishap",       (80,  115), "English"),
    ("Fury Road Reloaded",     "Action",      "cars,chase,explosion",         (100, 150), "English"),
    ("Iron Fist Chronicles",   "Action",      "martial-arts,hero,fight",      (95,  140), "English"),
    ("Siege Protocol",         "Action",      "military,war,strategy",        (110, 155), "English"),
    ("Always and Forever",     "Romance",     "love,marriage,emotion",        (100, 140), "English"),
    ("Monsoon Wedding Remix",  "Romance",     "india,love,family",            (105, 145), "Hindi"),
    ("Paris at Midnight",      "Romance",     "travel,love,europe",           (95,  135), "English"),
    ("Wild Earth Journeys",    "Documentary", "nature,wildlife,planet",       (60,  100), "English"),
    ("Inside the Algorithm",   "Documentary", "tech,ai,society",              (55,   90), "English"),
    ("Human Stories",          "Documentary", "people,culture,world",         (60,   95), "English"),
]

MUSIC_ENTRIES = [
    ("Summer Vibes",         "Pop",       "upbeat,dance,party",         (3,  5),  "English"),
    ("Neon Lights",          "Pop",       "synth,electro,catchy",       (3,  4),  "English"),
    ("City Pulse",           "Pop",       "modern,rhythm,feel-good",    (3,  5),  "English"),
    ("Garage Anthem",        "Rock",      "guitar,drums,energy",        (4,  6),  "English"),
    ("Steel Thunder",        "Rock",      "heavy,riff,classic",         (4,  7),  "English"),
    ("Broken Strings",       "Rock",      "alternative,indie,emotion",  (3,  6),  "English"),
    ("Street Hustler",       "Hip-Hop",   "rap,beats,flow",             (3,  5),  "English"),
    ("Gold Chain Theory",    "Hip-Hop",   "trap,bars,lyrical",          (3,  5),  "English"),
    ("Metro Nights",         "Hip-Hop",   "boom-bap,chill,underground", (3,  5),  "English"),
    ("Moonlight Sonata 2.0", "Classical", "piano,orchestral,serene",    (5,  15), "English"),
    ("Strings of Eternity",  "Classical", "violin,symphony,calm",       (6,  18), "English"),
    ("Rainy Study Session",  "Lo-fi",     "chill,study,calm,beats",     (30, 60), "English"),
    ("Coffee Shop Beats",    "Lo-fi",     "morning,relax,background",   (20, 45), "English"),
    ("Midnight Focus",       "Lo-fi",     "night,work,ambient",         (25, 50), "English"),
    ("Rooftop Dreams",       "Indie",     "acoustic,soft,indie",        (3,  5),  "English"),
    ("Wanderlust Melody",    "Indie",     "folk,guitar,travel",         (4,  6),  "English"),
    ("Dil Ki Baat",          "Bollywood", "hindi,emotion,filmy",        (4,  6),  "Hindi"),
    ("Naach Le",             "Bollywood", "dance,party,bhangra",        (4,  5),  "Hindi"),
    ("Pyaar Ka Safar",       "Bollywood", "romantic,soft,hindi",        (4,  6),  "Hindi"),
    ("Drop Zone",            "EDM",       "drop,bass,club",             (4,  7),  "English"),
    ("Festival Rush",        "EDM",       "trance,energy,rave",         (5,  8),  "English"),
    ("Deep Frequency",       "EDM",       "techno,house,groove",        (5,  8),  "English"),
]

VIDEO_ENTRIES = [
    ("Python in 60 Minutes",      "Education",    "python,programming,beginner",   (40,  75), "English"),
    ("Mathematics Made Simple",   "Education",    "math,concepts,school",          (30,  60), "English"),
    ("History Unlocked",          "Education",    "history,world,culture",         (20,  50), "English"),
    ("DSA Masterclass",           "Coding",       "algorithms,java,interview",     (60, 120), "English"),
    ("Build a REST API",          "Coding",       "fastapi,backend,python",        (45,  90), "English"),
    ("React Crash Course",        "Coding",       "javascript,frontend,react",     (50, 100), "English"),
    ("Full Stack in a Weekend",   "Coding",       "fullstack,node,mongo",          (90, 180), "English"),
    ("Morning Routine 2024",      "Productivity", "habits,health,morning",         (10,  25), "English"),
    ("Deep Work Explained",       "Productivity", "focus,work,flow-state",         (15,  30), "English"),
    ("Notion Setup for Students", "Productivity", "notion,organize,study",         (20,  40), "English"),
    ("GTA 6 Full Gameplay",       "Gaming",       "gta,open-world,rockstar",       (30,  90), "English"),
    ("Minecraft Mega Build",      "Gaming",       "minecraft,build,creative",      (20,  60), "English"),
    ("Valorant Pro Tips",         "Gaming",       "fps,strategy,esports",          (15,  45), "English"),
    ("Week in My Life - Tokyo",   "Vlogs",        "travel,japan,lifestyle",        (15,  35), "English"),
    ("College Life Diaries",      "Vlogs",        "student,daily,fun",             (10,  25), "English"),
    ("Budget Travel Europe",      "Vlogs",        "travel,budget,backpacking",     (20,  40), "English"),
    ("Tech Talk Weekly",          "Podcasts",     "tech,ai,interview,opinion",     (30,  60), "English"),
    ("Startup Stories",           "Podcasts",     "entrepreneur,business,growth",  (25,  55), "English"),
    ("Mind and Body Podcast",     "Podcasts",     "mental-health,wellness,habits", (20,  50), "English"),
    ("Stock Market 101",          "Finance",      "investing,stocks,beginner",     (30,  60), "English"),
    ("Crypto Deep Dive",          "Finance",      "crypto,bitcoin,blockchain",     (25,  50), "English"),
    ("Personal Finance Basics",   "Finance",      "budget,savings,money",          (20,  45), "English"),
    ("AI Tools for Everyone",     "Tech",         "ai,tools,productivity",         (15,  35), "English"),
    ("Linux for Beginners",       "Tech",         "linux,terminal,open-source",    (30,  60), "English"),
    ("Hardware Build Guide",      "Tech",         "pc,build,components",           (25,  50), "English"),
]


# ──────────────────────────────────────────────
# PERSONA DEFINITIONS
# ──────────────────────────────────────────────

PERSONAS = [
    {
        "name": "movie_fan",
        "weight": 0.17,
        "preferred_genres": [
            "Sci-Fi", "Horror", "Thriller", "Drama",
            "Comedy", "Action", "Romance", "Documentary",
        ],
        "event_weights": {
            "play": 30, "pause": 15, "skip": 10,
            "like": 25, "dislike": 5, "watch_complete": 15,
        },
    },
    {
        "name": "music_lover",
        "weight": 0.17,
        "preferred_genres": [
            "Pop", "Rock", "Hip-Hop", "Classical",
            "Lo-fi", "Indie", "Bollywood", "EDM",
        ],
        "event_weights": {
            "play": 35, "pause": 10, "skip": 10,
            "like": 30, "dislike": 5, "watch_complete": 10,
        },
    },
    {
        "name": "binge_watcher",
        "weight": 0.16,
        "preferred_genres": ["Drama", "Sci-Fi", "Action", "Thriller", "Horror"],
        "event_weights": {
            "play": 25, "pause": 10, "skip": 5,
            "like": 20, "dislike": 3, "watch_complete": 37,
        },
    },
    {
        "name": "short_attention_user",
        "weight": 0.17,
        "preferred_genres": ["Vlogs", "Gaming", "Pop", "Comedy"],
        "event_weights": {
            "play": 20, "pause": 15, "skip": 45,
            "like": 8, "dislike": 7, "watch_complete": 5,
        },
    },
    {
        "name": "education_viewer",
        "weight": 0.17,
        "preferred_genres": [
            "Education", "Coding", "Productivity",
            "Finance", "Tech", "Podcasts",
        ],
        "event_weights": {
            "play": 30, "pause": 20, "skip": 5,
            "like": 25, "dislike": 3, "watch_complete": 17,
        },
    },
    {
        "name": "mixed_consumer",
        "weight": 0.16,
        "preferred_genres": [
            "Sci-Fi", "Pop", "Education", "Gaming", "Vlogs",
            "Finance", "Drama", "Rock", "Coding", "Romance",
        ],
        "event_weights": {
            "play": 28, "pause": 14, "skip": 14,
            "like": 18, "dislike": 8, "watch_complete": 18,
        },
    },
]


# ──────────────────────────────────────────────
# HELPER FUNCTIONS
# ──────────────────────────────────────────────

def _pick_persona():
    return random.choices(PERSONAS, weights=[p["weight"] for p in PERSONAS])[0]


def _weighted_event(event_weights):
    events  = list(event_weights.keys())
    weights = list(event_weights.values())
    return random.choices(events, weights=weights)[0]


def _random_timestamp():
    """Returns a random datetime within the last 6 months."""
    days_back    = random.randint(0, 180)
    hours_back   = random.randint(0, 23)
    minutes_back = random.randint(0, 59)
    return datetime.utcnow() - timedelta(
        days=days_back, hours=hours_back, minutes=minutes_back
    )


def _make_email(name, idx):
    providers = ["gmail.com", "yahoo.com", "outlook.com", "protonmail.com", "hotmail.com"]
    clean = name.lower().replace(" ", ".")
    return f"{clean}.{idx}@{random.choice(providers)}"


# ──────────────────────────────────────────────
# NAME POOLS
# ──────────────────────────────────────────────

FIRST_NAMES = [
    "Aarav", "Ananya", "Rohan", "Priya", "Vikram", "Neha", "Arjun", "Divya",
    "Karan", "Sneha", "Aditya", "Pooja", "Rahul", "Meera", "Siddharth",
    "James", "Emma", "Liam", "Olivia", "Noah", "Ava", "Ethan", "Sophia",
    "Lucas", "Mia", "Mason", "Isabella", "Logan", "Charlotte", "Jackson",
    "Carlos", "Maria", "Diego", "Ana", "Luis", "Elena", "Jorge", "Isabel",
    "Wei", "Mei", "Jun", "Ling", "Hao", "Yan", "Chen", "Fang",
    "Ali", "Fatima", "Omar", "Layla", "Hassan", "Nour", "Yusuf", "Sara",
]

LAST_NAMES = [
    "Sharma", "Patel", "Kumar", "Singh", "Gupta", "Verma", "Mehta", "Shah",
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Martinez",
    "Lee", "Kim", "Chen", "Wang", "Liu", "Zhang", "Yang",
    "Gonzalez", "Rodriguez", "Hernandez", "Lopez", "Perez", "Torres",
    "Ahmed", "Khan", "Ali", "Hassan", "Ibrahim", "Malik",
]


# ──────────────────────────────────────────────
# DATA GENERATION FUNCTIONS
# ──────────────────────────────────────────────

def generate_users(n):
    users = []
    for i in range(1, n + 1):
        first = random.choice(FIRST_NAMES)
        last  = random.choice(LAST_NAMES)
        name  = f"{first} {last}"
        users.append({
            "name":  name,
            "email": _make_email(name, i),
        })
    return users


def generate_content(n):
    movie_count = int(n * 0.30)
    music_count = int(n * 0.30)
    video_count = n - movie_count - music_count

    items = []

    def _expand(templates, count):
        for _ in range(count):
            title, genre, tags, dur_range, lang = random.choice(templates)
            suffix = random.randint(1, 9999)
            items.append({
                "title":    f"{title} #{suffix}",
                "genre":    genre,
                "tags":     tags,
                "duration": random.randint(*dur_range),
                "language": lang,
                "rating":   round(random.uniform(2.5, 5.0), 1),
            })

    _expand(MOVIE_ENTRIES, movie_count)
    _expand(MUSIC_ENTRIES, music_count)
    _expand(VIDEO_ENTRIES, video_count)

    random.shuffle(items)
    return items


def generate_interactions(user_rows, content_rows, n):
    # Build genre -> [content_id, ...] for persona-biased selection
    genre_to_ids = {}
    for c in content_rows:
        genre_to_ids.setdefault(c.genre, []).append(c.id)

    all_content_ids = [c.id for c in content_rows]

    # Each user gets a fixed persona for consistent behavior
    user_personas = {u.id: _pick_persona() for u in user_rows}

    interactions = []
    for _ in range(n):
        user    = random.choice(user_rows)
        persona = user_personas[user.id]

        # 70% chance: pick content that matches the persona's preferred genre
        if random.random() < 0.70:
            genre         = random.choice(persona["preferred_genres"])
            candidate_ids = genre_to_ids.get(genre, all_content_ids)
            content_id    = random.choice(candidate_ids)
        else:
            content_id = random.choice(all_content_ids)

        interactions.append({
            "user_id":    user.id,
            "content_id": content_id,
            "event_type": _weighted_event(persona["event_weights"]),
            "timestamp":  _random_timestamp(),
        })

    return interactions


# ──────────────────────────────────────────────
# BULK INSERT HELPER
# ──────────────────────────────────────────────

def bulk_insert(db, model, rows, label):
    total    = len(rows)
    inserted = 0
    for i in range(0, total, BATCH_SIZE):
        batch = rows[i : i + BATCH_SIZE]
        db.bulk_insert_mappings(model, batch)
        db.commit()
        inserted += len(batch)
        print(f"  [{label}] {inserted}/{total} inserted", end="\r")
    print(f"  [{label}] {total}/{total} inserted [OK]   ")


# ──────────────────────────────────────────────
# MAIN ENTRY POINT
# ──────────────────────────────────────────────

def seed():
    db = SessionLocal()
    try:
        print("\n[SEED] Starting database seed...\n")

        print("-> Step 1/3: Generating users...")
        user_dicts = generate_users(NUM_USERS)
        bulk_insert(db, User, user_dicts, "users")
        user_rows = db.query(User).all()

        print("-> Step 2/3: Generating content...")
        content_dicts = generate_content(NUM_CONTENT)
        bulk_insert(db, Content, content_dicts, "content")
        content_rows = db.query(Content).all()

        print("-> Step 3/3: Generating interaction events...")
        interaction_dicts = generate_interactions(user_rows, content_rows, NUM_INTERACTIONS)
        bulk_insert(db, InteractionEvent, interaction_dicts, "interaction_events")

        print("\n[DONE] Seed complete!")
        print(f"   Users               : {len(user_rows)}")
        print(f"   Content items       : {len(content_rows)}")
        print(f"   Interaction events  : {NUM_INTERACTIONS}")

    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Seed failed: {e}")
        sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    seed()
