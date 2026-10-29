import pytest

from app.services.scoring.scorer import (
    SkillMatch,
    Weights,
    blend,
    calibrate,
    experience_score,
    skill_coverage,
    stage1,
)
from app.services.scoring.skills import normalize_skill


def test_calibrate_bounds():
    assert calibrate(0.10, 0.15, 0.65) == 0
    assert calibrate(0.80, 0.15, 0.65) == 100
    assert calibrate(0.40, 0.15, 0.65) == pytest.approx(50)


def test_experience_unknown_is_50():
    assert experience_score(None, 3) == 50


def test_experience_no_minimum_is_100():
    assert experience_score(1, None) == 100
    assert experience_score(None, None) == 100
    assert experience_score(1, 0) == 100


def test_experience_ratio_capped():
    assert experience_score(2, 4) == 50
    assert experience_score(10, 4) == 100


def _m(req, required, matched):
    return SkillMatch(requirement=req, required=required, matched=matched)


def test_skill_coverage_weights_required_double():
    matches = [_m("python", True, True), _m("docker", False, False)]
    # required weight 2 matched, nice weight 1 missed -> 2/3
    assert skill_coverage(matches) == pytest.approx(66.6667, rel=1e-3)


def test_no_requirements_neutral():
    assert skill_coverage([]) == 50


def test_stage1_weighted_sum():
    w = Weights(semantic=0.4, skills=0.45, experience=0.15)
    assert stage1(50, 100, 0, w) == pytest.approx(20 + 45)


def test_weights_must_sum_to_one():
    with pytest.raises(ValueError):
        Weights(semantic=0.5, skills=0.5, experience=0.5)


def test_blend():
    assert blend(60, 80, 0.5) == 70
    assert blend(60, None, 0.5) == 60


def test_normalize_aliases():
    assert normalize_skill(" JS ") == "javascript"
    assert normalize_skill("K8s") == "kubernetes"
    assert normalize_skill("Postgres") == "postgresql"
    assert normalize_skill("C++") == "c++"
    assert normalize_skill("C#") == "c#"
    assert normalize_skill("Node.js") == "node.js"
    assert normalize_skill("Machine-Learning") == "machine learning"
