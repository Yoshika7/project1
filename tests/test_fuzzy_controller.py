"""
Tests for Pure Python Mamdani Fuzzy Controller.
"""

import pytest
from backend.app.fuzzy.membership import triangular_mf, trapezoidal_mf
from backend.app.fuzzy.fuzzy_controller import FuzzyController


def test_membership_functions():
    # Triangular: a=0.2, b=0.5, c=0.8
    assert triangular_mf(0.1, 0.2, 0.5, 0.8) == 0.0
    assert triangular_mf(0.5, 0.2, 0.5, 0.8) == 1.0
    assert abs(triangular_mf(0.35, 0.2, 0.5, 0.8) - 0.5) < 1e-4

    # Trapezoidal: a=0.1, b=0.3, c=0.7, d=0.9
    assert trapezoidal_mf(0.05, 0.1, 0.3, 0.7, 0.9) == 0.0
    assert trapezoidal_mf(0.5, 0.1, 0.3, 0.7, 0.9) == 1.0
    assert trapezoidal_mf(0.95, 0.1, 0.3, 0.7, 0.9) == 0.0


def test_fuzzy_output_ranges():
    fc = FuzzyController()
    res = fc.evaluate(diversity=0.5, improvement=0.2, severity=0.1)

    assert 0.05 <= res["mutation_rate"] <= 0.45
    assert 0.10 <= res["exploration_level"] <= 0.90
    assert isinstance(res["activated_rules"], list)
    assert len(res["activated_rules"]) > 0


def test_rule_1_activation():
    # IF diversity is LOW AND improvement is LOW -> mutation HIGH, exploration HIGH
    fc = FuzzyController()
    res = fc.evaluate(diversity=0.05, improvement=0.01, severity=0.0)

    assert "R1" in res["activated_rules"]
    assert res["mutation_rate"] > 0.25
    assert res["exploration_level"] > 0.55


def test_rule_4_activation():
    # IF disruption severity is HIGH -> mutation HIGH, exploration HIGH
    fc = FuzzyController()
    res = fc.evaluate(diversity=0.4, improvement=0.02, severity=0.95)

    assert "R4" in res["activated_rules"]
    assert res["mutation_rate"] > 0.30
    assert res["exploration_level"] > 0.60


def test_high_vs_low_disruption_response():
    """
    CRITICAL REQUIREMENT:
    Under otherwise identical diversity and improvement values:
    High disruption severity should produce stronger adaptive exploration/mutation
    than low disruption severity according to the defined fuzzy rules.
    """
    fc = FuzzyController()
    # Baseline condition: medium diversity, moderate improvement
    d_val = 0.50
    i_val = 0.25

    # Case A: Low disruption
    low_res = fc.evaluate(diversity=d_val, improvement=i_val, severity=0.05)

    # Case B: High disruption
    high_res = fc.evaluate(diversity=d_val, improvement=i_val, severity=0.90)

    # High disruption must trigger higher exploration and mutation
    assert high_res["mutation_rate"] > low_res["mutation_rate"]
    assert high_res["exploration_level"] > low_res["exploration_level"]
    assert "R4" in high_res["activated_rules"]
