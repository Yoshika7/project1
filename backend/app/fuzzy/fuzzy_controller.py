"""
Pure Python Mamdani Fuzzy Inference System for AdaptIQ-R.

Implements a complete three-input, two-output Mamdani FIS from scratch —
no third-party fuzzy libraries (scikit-fuzzy, etc.) are used.

Pipeline
--------
Inputs  : diversity ∈ [0, 1], improvement ∈ [0, 1], severity ∈ [0, 1]
Outputs : mutation_rate ∈ [0.05, 0.45], exploration_level ∈ [0.10, 0.90]

Inference Steps
---------------
1. **Fuzzification** — evaluate membership degrees for each input term.
2. **Rule Firing** — compute each rule's activation via Mamdani minimum
   implication over the antecedent membership degrees.
3. **Aggregation** — combine clipped consequent MFs using pointwise maximum.
4. **Defuzzification** — centroid method over 100 discrete samples.

Complexity Summary
------------------
- __init__   : O(R) where R = number of rules (fixed: 9)
- evaluate   : O(R * D) where D = discretization_steps (default: 100)
               — dominated by the aggregation loops
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from backend.app.core.config import (
    EXPLORATION_LEVEL_MAX,
    EXPLORATION_LEVEL_MIN,
    FUZZY_DIVERSITY_MF,
    FUZZY_EXPLORATION_MF,
    FUZZY_IMPROVEMENT_MF,
    FUZZY_MUTATION_MF,
    FUZZY_SEVERITY_MF,
    MUTATION_RATE_MAX,
    MUTATION_RATE_MIN,
)
from backend.app.fuzzy.membership import LinguisticVariable, evaluate_mf
from backend.app.fuzzy.rules import CORE_RULES, FuzzyRule

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

__all__ = ["FuzzyController"]


class FuzzyController:
    """Mamdani Fuzzy Inference System for online GA hyperparameter adaptation.

    This controller implements a classical Mamdani FIS that continuously
    re-tunes the Genetic Algorithm's mutation rate and population exploration
    level based on three real-valued feedback signals measured from the
    optimisation state:

    * **Diversity** — how structurally varied the current population is.
      Low diversity → increase mutation to escape local minima.
    * **Improvement** — how much the best fitness improved this generation.
      Low improvement → increase exploration to find new regions.
    * **Severity** — how disruptive the current environmental state is.
      High severity → spike mutation and exploration for rapid recovery.

    The FIS replaces hand-coded adaptive schedules with transparent,
    interpretable fuzzy rules that can be audited and extended.

    Parameters
    ----------
    discretization_steps:
        Number of discrete points used in the defuzzification numerical
        integration.  Higher values improve accuracy at linear cost.
        Default ``100`` gives < 0.5 ms inference latency.

    Attributes
    ----------
    var_diversity : LinguisticVariable
        Input variable with terms: LOW, MED, HIGH — universe [0, 1].
    var_improvement : LinguisticVariable
        Input variable with terms: LOW, MED, HIGH — universe [0, 1].
    var_severity : LinguisticVariable
        Input variable with terms: LOW, MED, HIGH — universe [0, 1].
    var_mutation : LinguisticVariable
        Output variable with terms: LOW, MED, HIGH —
        universe [MUTATION_RATE_MIN, MUTATION_RATE_MAX].
    var_exploration : LinguisticVariable
        Output variable with terms: LOW, MED, HIGH —
        universe [EXPLORATION_LEVEL_MIN, EXPLORATION_LEVEL_MAX].
    rules : List[FuzzyRule]
        The active rule base (9 core rules by default).

    Complexity
    ----------
    __init__ : O(R) — stores R rules.
    evaluate : O(R * D) — R rule firings × D defuzzification steps.
    """

    def __init__(self, discretization_steps: int = 100) -> None:
        # D — number of points in the defuzzification universe grid
        self.steps: int = discretization_steps

        # ------------------------------------------------------------------ #
        # Input linguistic variables                                          #
        # ------------------------------------------------------------------ #
        self.var_diversity = LinguisticVariable("diversity", 0.0, 1.0, FUZZY_DIVERSITY_MF)
        self.var_improvement = LinguisticVariable("improvement", 0.0, 1.0, FUZZY_IMPROVEMENT_MF)
        self.var_severity = LinguisticVariable("severity", 0.0, 1.0, FUZZY_SEVERITY_MF)

        # ------------------------------------------------------------------ #
        # Output linguistic variables                                         #
        # ------------------------------------------------------------------ #
        self.var_mutation = LinguisticVariable(
            "mutation", MUTATION_RATE_MIN, MUTATION_RATE_MAX, FUZZY_MUTATION_MF
        )
        self.var_exploration = LinguisticVariable(
            "exploration", EXPLORATION_LEVEL_MIN, EXPLORATION_LEVEL_MAX, FUZZY_EXPLORATION_MF
        )

        # 9 core rules loaded from the rule-base module
        self.rules: List[FuzzyRule] = list(CORE_RULES)

    def evaluate(
        self,
        diversity: float,
        improvement: float,
        severity: float,
    ) -> Dict[str, Any]:
        """Run Mamdani inference and return defuzzified parameter values.

        Executes the full four-stage Mamdani pipeline:

        **Stage 1 — Fuzzification**

        Each crisp input is converted to a membership-degree dictionary over
        its defined linguistic terms using the configured MF shapes::

            μ_LOW(diversity), μ_MED(diversity), μ_HIGH(diversity) ...

        **Stage 2 — Rule Activation (min implication)**

        For each rule, the firing strength α is computed as the minimum
        membership degree across all antecedent terms:

        .. math::
            \\alpha_r = \\min_{(v, t) \\in \\text{antecedents}_r} \\mu_t(v)

        Rules with α ≤ 0.005 (below numerical noise threshold) are skipped.

        **Stage 3 — Aggregation (pointwise maximum)**

        For each output universe sample *y*, the aggregated membership is the
        maximum clipped consequent MF degree across all fired rules:

        .. math::
            \\mu_{\\text{agg}}(y) = \\max_r \\min(\\alpha_r,\\ \\mu_{\\text{term}_r}(y))

        **Stage 4 — Centroid Defuzzification**

        The crisp output is computed as the centre of mass of the aggregated
        distribution:

        .. math::
            y^* = \\frac{\\sum_j y_j \\cdot \\mu_{\\text{agg}}(y_j)}
                        {\\sum_j \\mu_{\\text{agg}}(y_j)}

        If no rules fire (all α = 0), the output defaults to the midpoint of
        the output universe.

        Parameters
        ----------
        diversity:
            Population diversity signal in ``[0, 1]``.  Values outside this
            range are clamped before inference.
        improvement:
            Normalised fitness improvement in ``[0, 1]``.  Values outside
            this range are clamped.
        severity:
            Disruption severity in ``[0, 1]``.  Values outside this range
            are clamped.

        Returns
        -------
        Dict[str, Any]
            Dictionary with three keys:

            * ``"mutation_rate"`` (float) — defuzzified mutation probability
              in ``[MUTATION_RATE_MIN, MUTATION_RATE_MAX]``.
            * ``"exploration_level"`` (float) — defuzzified exploration level
              in ``[EXPLORATION_LEVEL_MIN, EXPLORATION_LEVEL_MAX]``.
            * ``"activated_rules"`` (List[str]) — IDs of rules with α > 0.005.

        Complexity
        ----------
        Time : O(R * D) where R = number of rules, D = discretization_steps.
        Space: O(D) for the two aggregated MF arrays (mutation + exploration).
        """
        # ------------------------------------------------------------------ #
        # Stage 1: Clamp inputs and fuzzify — O(R) total                     #
        # ------------------------------------------------------------------ #
        d_val = max(0.0, min(1.0, float(diversity)))
        i_val = max(0.0, min(1.0, float(improvement)))
        s_val = max(0.0, min(1.0, float(severity)))

        # Returns Dict[term_name, membership_degree] for each input variable
        fuzz_d = self.var_diversity.fuzzify(d_val)
        fuzz_i = self.var_improvement.fuzzify(i_val)
        fuzz_s = self.var_severity.fuzzify(s_val)

        input_memberships: Dict[str, Dict[str, float]] = {
            "diversity": fuzz_d,
            "improvement": fuzz_i,
            "severity": fuzz_s,
        }

        # ------------------------------------------------------------------ #
        # Stage 2: Rule evaluation — Mamdani min implication — O(R)          #
        # ------------------------------------------------------------------ #
        activated_rules: List[str] = []
        # Each entry: (firing_strength, consequent_term_dict)
        rule_firings: List[Tuple[float, Dict[str, str]]] = []

        for rule in self.rules:
            # Minimum membership across all antecedent conditions
            strengths = [
                input_memberships[var_name].get(term, 0.0)
                for var_name, term in rule.antecedents.items()
            ]
            firing_strength: float = min(strengths) if strengths else 0.0

            # Threshold below which rule contribution is negligible (numerical noise)
            if firing_strength > 0.005:
                activated_rules.append(rule.rule_id)
                rule_firings.append((firing_strength, rule.consequents))

        # ------------------------------------------------------------------ #
        # Stage 3 & 4: Aggregation + Centroid Defuzzification for Mutation   #
        # O(R * D)                                                            #
        # ------------------------------------------------------------------ #
        mut_range = MUTATION_RATE_MAX - MUTATION_RATE_MIN
        # Pre-compute the D universe sample points — O(D)
        mut_samples = [
            MUTATION_RATE_MIN + j * mut_range / (self.steps - 1)
            for j in range(self.steps)
        ]
        # mut_agg[j] = aggregated (max) membership at universe point j
        mut_agg = [0.0] * self.steps

        for firing_strength, consequents in rule_firings:  # O(R)
            mut_term = consequents.get("mutation")
            if mut_term:
                params = self.var_mutation.terms[mut_term]
                for j, y in enumerate(mut_samples):  # O(D)
                    # Clipped MF value — Mamdani min(α, μ(y))
                    implicated = min(firing_strength, evaluate_mf(y, params))
                    if implicated > mut_agg[j]:
                        mut_agg[j] = implicated  # Pointwise max aggregation

        # Centroid defuzzification for mutation — O(D)
        sum_weights = sum(mut_agg)
        if sum_weights > 1e-9:
            centroid_mut = (
                sum(y * mu for y, mu in zip(mut_samples, mut_agg)) / sum_weights
            )
        else:
            # Fallback to universe midpoint when no rules fire
            centroid_mut = (MUTATION_RATE_MIN + MUTATION_RATE_MAX) / 2.0

        # ------------------------------------------------------------------ #
        # Stage 3 & 4: Aggregation + Centroid Defuzzification for Exploration #
        # O(R * D)                                                            #
        # ------------------------------------------------------------------ #
        exp_range = EXPLORATION_LEVEL_MAX - EXPLORATION_LEVEL_MIN
        exp_samples = [
            EXPLORATION_LEVEL_MIN + j * exp_range / (self.steps - 1)
            for j in range(self.steps)
        ]
        exp_agg = [0.0] * self.steps

        for firing_strength, consequents in rule_firings:  # O(R)
            exp_term = consequents.get("exploration")
            if exp_term:
                params = self.var_exploration.terms[exp_term]
                for j, z in enumerate(exp_samples):  # O(D)
                    implicated = min(firing_strength, evaluate_mf(z, params))
                    if implicated > exp_agg[j]:
                        exp_agg[j] = implicated

        # Centroid defuzzification for exploration — O(D)
        sum_exp_weights = sum(exp_agg)
        if sum_exp_weights > 1e-9:
            centroid_exp = (
                sum(z * mu for z, mu in zip(exp_samples, exp_agg)) / sum_exp_weights
            )
        else:
            centroid_exp = (EXPLORATION_LEVEL_MIN + EXPLORATION_LEVEL_MAX) / 2.0

        # ------------------------------------------------------------------ #
        # Final clamping to valid output ranges                               #
        # ------------------------------------------------------------------ #
        final_mutation = max(MUTATION_RATE_MIN, min(MUTATION_RATE_MAX, centroid_mut))
        final_exploration = max(
            EXPLORATION_LEVEL_MIN, min(EXPLORATION_LEVEL_MAX, centroid_exp)
        )

        return {
            "mutation_rate": round(final_mutation, 4),
            "exploration_level": round(final_exploration, 4),
            "activated_rules": activated_rules,
        }
