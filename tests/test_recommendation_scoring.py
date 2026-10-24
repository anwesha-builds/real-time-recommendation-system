from app.services.recommendation_service import combine_genre_scores


def test_combine_genre_scores_blends_historical_and_session():
    historical_scores = {"Horror": 10, "Comedy": 2}
    session_scores = {"Horror": 0, "Tech": 5}

    result = combine_genre_scores(historical_scores, session_scores)

    assert result["Horror"] == 10 * 0.6
    assert result["Comedy"] == 2 * 0.6
    assert result["Tech"] == 5 * 0.4


def test_combine_genre_scores_handles_no_overlap():
    result = combine_genre_scores({"Horror": 4}, {"Comedy": 8})

    assert result == {"Horror": 4 * 0.6, "Comedy": 8 * 0.4}


def test_combine_genre_scores_handles_empty_input():
    assert combine_genre_scores({}, {}) == {}
