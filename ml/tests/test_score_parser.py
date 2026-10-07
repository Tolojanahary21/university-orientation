import pytest

from orientation_ml.ocr.score_parser import NoScoresFound, parse_scores


@pytest.mark.parametrize(("text", "expected"), [("Mathématiques : 16/20", 16), ("Maths 8/10", 16), ("English 75/100", 15), ("Français : 12,50", 12.5)])
def test_parse_and_scale_scores(text, expected):
    scores, warnings = parse_scores(text)
    assert scores[0].value == expected
    assert warnings == []


def test_rejects_out_of_range_without_denominator():
    with pytest.raises(NoScoresFound):
        parse_scores("Maths 75")


def test_parses_table_rows_with_coefficient_and_maximum():
    scores, _ = parse_scores(
        "Mathématiques Générales 4 61,00 80\n"
        "Sciences Naturelles 4 43,00 80\n"
        "Sciences Physiques 4 20,00 80\n"
        "Malagasy 3 31,50 60\n"
        "Français 2 23,00 40\n"
        "Histoire - Géographie 2 26,00 40\n"
        "Philosophie 2 20,00 40\n"
        "Anglais (Facultative) BONI 00,00 10"
    )
    assert [score.subject for score in scores] == [
        "mathematics",
        "biology",
        "physics_chemistry",
        "malagasy",
        "french",
        "history_geography",
        "philosophy",
        "english",
    ]
    assert [score.normalized_score for score in scores] == [15.25, 10.75, 5, 10.5, 11.5, 13, 10, 0]
    assert [score.coefficient for score in scores] == [4, 4, 4, 3, 2, 2, 2, None]
    assert scores[0].raw_score == 61 and scores[0].max_score == 80
    assert scores[-1].optional is True


def test_table_note_without_maximum_is_not_assumed_to_be_out_of_twenty():
    with pytest.raises(NoScoresFound):
        parse_scores("Matières Note Max\nSciences Physiques 4 20,00")


def test_bac_fixture_extracts_columns_and_corrects_numeric_ocr_o():
    fixture = """Option D
Année 2023
Matières Coef Note Max
Mathématiques Générales 4 61,00 80
Sciences Naturelles 4 43,00 80
Sciences Physiques 4 O8,50 80
Malagasy 3 31,50 60
Français 2 23,00 40
Histoire-Géographie 2 26,00 40
Philosophie 2 20,00 40
EPS 1 08,50 20
Anglais Facultative BONI 00,00 10
Moyenne : 11,59
Mention : Passable"""
    scores, warnings = parse_scores(fixture)
    assert len(scores) == 9
    assert scores[2].raw_subject == "Sciences Physiques"
    assert scores[2].raw_score == 8.5
    assert scores[2].max_score == 80
    assert scores[2].normalized_score == 2.12
    assert scores[2].coefficient == 4
    assert scores[-1].optional is True
    assert warnings == []

