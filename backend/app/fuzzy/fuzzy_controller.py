"""
Pure Python Mamdani Fuzzy Controller for AdaptIQ-R.
Performs fuzzification, min-implication, max-aggregation, and centroid defuzzification.
"""

from typing import Dict, List, Tuple, Any
from backend.app.core.config import (
    FUZZY_DIVERSITY_MF,
    FUZZY_IMPROVEMENT_MF,
    FUZZY_SEVERITY_MF,
    FUZZY_MUTATION_MF,
    FUZZY_EXPLORATION_MF,
    MUTATION_RATE_MIN,
    MUTATION_RATE_MAX,
    EXPLORATION_LEVEL_MIN,
    EXPLORATION_LEVEL_MAX
)
from backend.app.fuzzy.membership import LinguisticVariable, evaluate_mf
from backend.app.fuzzy.rules import CORE_RULES, FuzzyRule


class FuzzyController:
    """
    Adaptive parameter tuner using Mamdani Fuzzy Inference.
    Dynamically modulates Genetic Algorithm mutation rate and exploration level.
    """

    def __init__(self, discretization_steps: int = 100):
        self.steps = discretization_steps

        # Initialize input linguistic variables
        self.var_diversity = LinguisticVariable("diversity", 0.0, 1.0, FUZZY_DIVERSITY_MF)
        self.var_improvement = LinguisticVariable("improvement", 0.0, 1.0, FUZZY_IMPROVEMENT_MF)
        self.var_severity = LinguisticVariable("severity", 0.0, 1.0, FUZZY_SEVERITY_MF)

        # Initialize output linguistic variables
        self.var_mutation = LinguisticVariable("mutation", MUTATION_RATE_MIN, MUTATION_RATE_MAX, FUZZY_MUTATION_MF)
        self.var_exploration = LinguisticVariable("exploration", EXPLORATION_LEVEL_MIN, EXPLORATION_LEVEL_MAX, FUZZY_EXPLORATION_MF)

        self.rules: List[FuzzyRule] = list(CORE_RULES)

    def evaluate(
        self,
        diversity: float,
        improvement: float,
        severity: float
    ) -> Dict[str, Any]:
        """
        Executes Mamdani inference and centroid defuzzification.
        Inputs clamped to [0, 1].
        """
        d_val = max(0.0, min(1.0, float(diversity)))
        i_val = max(0.0, min(1.0, float(improvement)))
        s_val = max(0.0, min(1.0, float(severity)))

        # 1. Fuzzification
        fuzz_d = self.var_diversity.fuzzify(d_val)
        fuzz_i = self.var_improvement.fuzzify(i_val)
        fuzz_s = self.var_severity.fuzzify(s_val)

        input_memberships = {
            "diversity": fuzz_d,
            "improvement": fuzz_i,
            "severity": fuzz_s
        }

        # 2. Rule evaluation (Mamdani min implication)
        activated_rules: List[str] = []
        rule_firings: List[Tuple[float, Dict[str, str]]] = []

        for rule in self.rules:
            strengths = []
            for var_name, term in rule.antecedents.items():
                degree = input_memberships[var_name].get(term, 0.0)
                strengths.append(degree)

            firing_strength = min(strengths) if strengths else 0.0

            if firing_strength > 0.005:
                activated_rules.append(rule.rule_id)
                rule_firings.append((firing_strength, rule.consequents))

        # 3. Discretized Max-Aggregation & Centroid Defuzzification for Mutation
        mut_samples = [
            MUTATION_RATE_MIN + j * (MUTATION_RATE_MAX - MUTATION_RATE_MIN) / (self.steps - 1)
            for j in range(self.steps)
        ]
        mut_agg = [0.0] * self.steps

        for firing_strength, consequents in rule_firings:
            mut_term = consequents.get("mutation")
            if mut_term:
                params = self.var_mutation.terms[mut_term]
                for j, y in enumerate(mut_samples):
                    term_mf = evaluate_mf(y, params)
                    implicated = min(firing_strength, term_mf)
                    if implicated > mut_agg[j]:
                        mut_agg[j] = implicated

        # Centroid defuzzification for mutation
        sum_weights = sum(mut_agg)
        if sum_weights > 1e-9:
            centroid_mut = sum(y * mu for y, mu in zip(mut_samples, mut_agg)) / sum_weights
        else:
            centroid_mut = (MUTATION_RATE_MIN + MUTATION_RATE_MAX) / 2.0

        # 4. Discretized Max-Aggregation & Centroid Defuzzification for Exploration
        exp_samples = [
            EXPLORATION_LEVEL_MIN + j * (EXPLORATION_LEVEL_MAX - EXPLORATION_LEVEL_MIN) / (self.steps - 1)
            for j in range(self.steps)
        ]
        exp_agg = [0.0] * self.steps

        for firing_strength, consequents in rule_firings:
            exp_term = consequents.get("exploration")
            if exp_term:
                params = self.var_exploration.terms[exp_term]
                for j, z in enumerate(exp_samples):
                    term_mf = evaluate_mf(z, params)
                    implicated = min(firing_strength, term_mf)
                    if implicated > exp_agg[j]:
                        exp_agg[j] = implicated

        # Centroid defuzzification for exploration
        sum_exp_weights = sum(exp_agg)
        if sum_exp_weights > 1e-9:
            centroid_exp = sum(z * mu for z, mu in zip(exp_samples, exp_agg)) / sum_exp_weights
        else:
            centroid_exp = (EXPLORATION_LEVEL_MIN + EXPLORATION_LEVEL_MAX) / 2.0

        # Ensure output bounds
        final_mutation = max(MUTATION_RATE_MIN, min(MUTATION_RATE_MAX, centroid_mut))
        final_exploration = max(EXPLORATION_LEVEL_MIN, min(EXPLORATION_LEVEL_MAX, centroid_exp))

        return {
            "mutation_rate": round(final_mutation, 4),
            "exploration_level": round(final_exploration, 4),
            "activated_rules": activated_rules
        }
