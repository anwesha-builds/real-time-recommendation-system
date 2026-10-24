import time

import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from app.models.interaction import InteractionEvent
from app.constants import EVENT_WEIGHTS

CACHE_REFRESH_SECONDS = 600

_cache = {
    "built_at": 0,
    "interaction_matrix": None,
    "item_similarity": None
}


def _build_matrices(db):
    """user x content interaction-weight matrix, and the item-item
    cosine similarity derived from it."""

    rows = (
        db.query(
            InteractionEvent.user_id,
            InteractionEvent.content_id,
            InteractionEvent.event_type
        )
        .all()
    )

    if not rows:
        return None, None

    df = pd.DataFrame(
        [
            {
                "user_id": r.user_id,
                "content_id": r.content_id,
                "weight": EVENT_WEIGHTS.get(r.event_type, 0)
            }
            for r in rows
        ]
    )

    interaction_matrix = (
        df.groupby(["user_id", "content_id"])["weight"]
        .sum()
        .unstack(fill_value=0)
    )

    item_vectors = interaction_matrix.T

    similarity = cosine_similarity(item_vectors)

    item_similarity = pd.DataFrame(
        similarity,
        index=item_vectors.index,
        columns=item_vectors.index
    )

    return interaction_matrix, item_similarity


def _get_cached_matrices(db):
    now = time.time()

    stale = (
        _cache["interaction_matrix"] is None
        or now - _cache["built_at"] > CACHE_REFRESH_SECONDS
    )

    if stale:
        interaction_matrix, item_similarity = _build_matrices(db)
        _cache["interaction_matrix"] = interaction_matrix
        _cache["item_similarity"] = item_similarity
        _cache["built_at"] = now

    return (
        _cache["interaction_matrix"],
        _cache["item_similarity"]
    )


def score_candidates(interaction_matrix, item_similarity, user_id, candidate_ids):
    """Pure function (no DB/Redis) so it's easy to unit test.

    For each candidate, looks at how similar it is to content the user
    already liked, weighted by how much they liked it. Returns a score
    roughly in [-1, 1] per candidate_id (only candidates with a usable
    signal are included).
    """

    scores = {}

    if interaction_matrix is None or user_id not in interaction_matrix.index:
        return scores

    user_row = interaction_matrix.loc[user_id]
    liked_items = user_row[user_row > 0]

    if liked_items.empty:
        return scores

    for content_id in candidate_ids:
        if content_id not in item_similarity.index:
            continue

        similarities = (
            item_similarity.loc[content_id, liked_items.index]
            .clip(lower=0)
        )

        if similarities.sum() == 0:
            scores[content_id] = 0.0
            continue

        weighted_preference = (
            (similarities * liked_items).sum() / similarities.sum()
        )

        scores[content_id] = max(
            -1.0,
            min(1.0, weighted_preference / 5)
        )

    return scores


def get_collaborative_scores(db, user_id, candidate_ids):
    interaction_matrix, item_similarity = _get_cached_matrices(db)

    if interaction_matrix is None:
        return {}

    return score_candidates(
        interaction_matrix,
        item_similarity,
        user_id,
        candidate_ids
    )
