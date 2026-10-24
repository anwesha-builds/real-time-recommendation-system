import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from app.services.collaborative_filtering import score_candidates


def _build_test_matrices():
    # user 1 liked item 10 only.
    # user 2 liked both item 10 and item 20 -> they look similar.
    # user 3 liked item 30 only -> unrelated to 10/20.
    interaction_matrix = pd.DataFrame(
        {
            10: [5, 5, 0],
            20: [0, 5, 0],
            30: [0, 0, 5]
        },
        index=[1, 2, 3]
    )

    item_vectors = interaction_matrix.T
    similarity = cosine_similarity(item_vectors)

    item_similarity = pd.DataFrame(
        similarity,
        index=item_vectors.index,
        columns=item_vectors.index
    )

    return interaction_matrix, item_similarity


def test_score_candidates_favors_items_similar_to_liked_content():
    interaction_matrix, item_similarity = _build_test_matrices()

    scores = score_candidates(
        interaction_matrix,
        item_similarity,
        user_id=1,
        candidate_ids=[20, 30]
    )

    assert scores[20] > scores[30]
    assert scores[30] == 0.0


def test_score_candidates_returns_empty_for_unknown_user():
    interaction_matrix, item_similarity = _build_test_matrices()

    scores = score_candidates(
        interaction_matrix,
        item_similarity,
        user_id=999,
        candidate_ids=[10]
    )

    assert scores == {}


def test_score_candidates_returns_empty_when_matrix_missing():
    scores = score_candidates(
        None,
        None,
        user_id=1,
        candidate_ids=[10]
    )

    assert scores == {}
