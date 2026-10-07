from pathlib import Path

from app.scales import load_scales
from app.scoring import score

VALID = {"answers": {"e1": 4, "e2": 2, "a1": 5, "a2": 1}}


def submit(client, answers, scale_id="ipip-mini"):
    return client.post(f"/scales/{scale_id}/submissions", json={"answers": answers})


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_list_scales(client):
    response = client.get("/scales")
    assert response.status_code == 200
    assert response.json() == [
        {
            "id": "ipip-mini",
            "name": "IPIP mini example",
            "item_count": 4,
            "subscales": ["agreeableness", "extraversion"],
        }
    ]


def test_get_scale_hides_scoring_key(client):
    response = client.get("/scales/ipip-mini")
    assert response.status_code == 200
    body = response.json()
    assert body["items"][0] == {"id": "e1", "text": "Am the life of the party."}
    assert "version" not in body
    assert all(set(item) == {"id", "text"} for item in body["items"])


def test_unknown_scale_is_404_on_every_route(client):
    assert client.get("/scales/nope").status_code == 404
    assert client.get("/scales/nope/stats").status_code == 404
    assert submit(client, VALID["answers"], scale_id="nope").status_code == 404


def test_valid_submission(client):
    response = client.post("/scales/ipip-mini/submissions", json=VALID)
    assert response.status_code == 201
    body = response.json()
    assert body["scores"] == {"agreeableness": 5.0, "extraversion": 4.0}
    assert response.headers["location"] == f"/submissions/{body['id']}"
    assert body["created_at"].endswith("Z")


def test_invalid_submission_lists_problems_and_stores_nothing(client):
    response = submit(client, {"e1": 4, "a1": 7, "a2": 1, "x9": 3})
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {"item": "e2", "error": "missing"},
            {"item": "x9", "error": "unknown item"},
            {"item": "a1", "error": "value 7 outside 1-5"},
        ]
    }
    assert client.get("/scales/ipip-mini/stats").json()["n"] == 0


def test_strings_and_floats_are_rejected(client):
    assert submit(client, {"e1": "4", "e2": 2, "a1": 5, "a2": 1}).status_code == 422
    assert submit(client, {"e1": 4.0, "e2": 2, "a1": 5, "a2": 1}).status_code == 422


def test_empty_answers_rejected(client):
    assert submit(client, {}).status_code == 422


def test_submit_then_fetch(client):
    created = client.post("/scales/ipip-mini/submissions", json=VALID).json()
    response = client.get(f"/submissions/{created['id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["answers"] == VALID["answers"]
    assert body["scores"] == created["scores"]
    assert body["created_at"] == created["created_at"]


def test_unknown_submission_is_404(client):
    assert client.get("/submissions/999").status_code == 404


def test_stats_with_no_submissions(client):
    assert client.get("/scales/ipip-mini/stats").json() == {
        "scale_id": "ipip-mini",
        "n": 0,
        "subscales": {
            "agreeableness": {"mean": None, "sd": None},
            "extraversion": {"mean": None, "sd": None},
        },
    }


def test_stats_with_one_submission(client):
    submit(client, VALID["answers"])
    stats = client.get("/scales/ipip-mini/stats").json()
    assert stats["n"] == 1
    assert stats["subscales"]["extraversion"] == {"mean": 4.0, "sd": None}


def test_stats_with_three_submissions(client):
    # Extraversion scores 4.0, 2.0, 3.0 -> mean 3.0, SD 1.0; agreeableness always 3.0.
    for e1, e2 in [(4, 2), (2, 4), (3, 3)]:
        submit(client, {"e1": e1, "e2": e2, "a1": 3, "a2": 3})
    stats = client.get("/scales/ipip-mini/stats").json()
    assert stats["n"] == 3
    assert stats["subscales"]["extraversion"] == {"mean": 3.0, "sd": 1.0}
    assert stats["subscales"]["agreeableness"] == {"mean": 3.0, "sd": 0.0}


def test_bundled_big_five_scale_is_valid():
    scales = load_scales(Path(__file__).parent.parent / "scales")
    bfm = scales["ipip-bfm-50"]
    assert len(bfm.items) == 50
    assert all(sum(i.subscale == s for i in bfm.items) == 10 for s in bfm.subscales)
    assert score(bfm, {item.id: 3 for item in bfm.items}) == {s: 3.0 for s in bfm.subscales}
