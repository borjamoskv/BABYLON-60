from __future__ import annotations

from apex_trials.ctgov import classify_history


def _hist(*versions: dict[str, object]) -> dict[str, object]:
    return {'changes': list(versions)}

def test_v0_is_not_an_amendment() -> None:
    h = classify_history('NCT1', _hist({'version': 0, 'date': '2020-01-01', 'moduleLabels': []}))
    assert h.n_substantive == 0 and h.n_administrative == 0 and (h.n_versions == 1)

def test_substantive_modules_counted() -> None:
    h = classify_history('NCT1', _hist({'version': 0, 'date': '2020-01-01', 'moduleLabels': []}, {'version': 1, 'date': '2020-06-01', 'moduleLabels': ['Eligibility']}, {'version': 2, 'date': '2021-01-01', 'moduleLabels': ['Study Design', 'Study Status']}, {'version': 3, 'date': '2021-06-01', 'moduleLabels': ['Outcome Measures']}))
    assert h.n_substantive == 3
    assert h.substantive_dates == ('2020-06-01', '2021-01-01', '2021-06-01')

def test_administrative_not_counted_as_substantive() -> None:
    h = classify_history('NCT1', _hist({'version': 0, 'date': '2020-01-01', 'moduleLabels': []}, {'version': 1, 'date': '2020-06-01', 'moduleLabels': ['Study Status']}, {'version': 2, 'date': '2021-01-01', 'moduleLabels': ['Contacts/Locations', 'Sponsor/Collaborators']}))
    assert h.n_substantive == 0 and h.n_administrative == 2

def test_results_sections_excluded_entirely() -> None:
    h = classify_history('NCT1', _hist({'version': 0, 'date': '2020-01-01', 'moduleLabels': []}, {'version': 1, 'date': '2022-01-01', 'moduleLabels': ['Outcome Measures (Results)', 'Adverse Events']}, {'version': 2, 'date': '2022-02-01', 'moduleLabels': ['Participant Flow', 'Baseline Characteristics']}))
    assert h.n_substantive == 0 and h.n_administrative == 0
    assert not h.unknown_labels

def test_unknown_label_surfaced() -> None:
    h = classify_history('NCT1', _hist({'version': 1, 'date': '2020-06-01', 'moduleLabels': ['Totally New Section']}))
    assert 'Totally New Section' in h.unknown_labels