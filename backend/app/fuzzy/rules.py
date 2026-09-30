"""
Fuzzy Rule Base for AdaptIQ-R.
Encodes the 7 core Mamdani rules and antecedent min-conjunctions.
"""

from typing import Dict, List, Tuple, Any
from pydantic import BaseModel


class FuzzyRule(BaseModel):
    rule_id: str
    description: str
    antecedents: Dict[str, str]  # e.g. {"diversity": "LOW", "improvement": "LOW"}
    consequents: Dict[str, str]  # e.g. {"mutation": "HIGH", "exploration": "HIGH"}


# The 7 core competition research rules specified in Section 10
CORE_RULES: List[FuzzyRule] = [
    FuzzyRule(
        rule_id="R1",
        description="IF diversity is LOW AND fitness improvement is LOW THEN mutation is HIGH AND exploration is HIGH",
        antecedents={"diversity": "LOW", "improvement": "LOW"},
        consequents={"mutation": "HIGH", "exploration": "HIGH"}
    ),
    FuzzyRule(
        rule_id="R2",
        description="IF diversity is LOW AND fitness improvement is MEDIUM THEN mutation is HIGH AND exploration is MEDIUM",
        antecedents={"diversity": "LOW", "improvement": "MEDIUM"},
        consequents={"mutation": "HIGH", "exploration": "MEDIUM"}
    ),
    FuzzyRule(
        rule_id="R3",
        description="IF diversity is HIGH AND fitness improvement is HIGH THEN mutation is LOW AND exploration is LOW",
        antecedents={"diversity": "HIGH", "improvement": "HIGH"},
        consequents={"mutation": "LOW", "exploration": "LOW"}
    ),
    FuzzyRule(
        rule_id="R4",
        description="IF disruption severity is HIGH THEN mutation is HIGH AND exploration is HIGH",
        antecedents={"severity": "HIGH"},
        consequents={"mutation": "HIGH", "exploration": "HIGH"}
    ),
    FuzzyRule(
        rule_id="R5",
        description="IF disruption severity is MEDIUM AND improvement is LOW THEN mutation is HIGH AND exploration is MEDIUM",
        antecedents={"severity": "MEDIUM", "improvement": "LOW"},
        consequents={"mutation": "HIGH", "exploration": "MEDIUM"}
    ),
    FuzzyRule(
        rule_id="R6",
        description="IF disruption severity is LOW AND improvement is HIGH THEN mutation is LOW AND exploration is LOW",
        antecedents={"severity": "LOW", "improvement": "HIGH"},
        consequents={"mutation": "LOW", "exploration": "LOW"}
    ),
    FuzzyRule(
        rule_id="R7",
        description="IF diversity is MEDIUM AND improvement is MEDIUM THEN mutation is MEDIUM AND exploration is MEDIUM",
        antecedents={"diversity": "MEDIUM", "improvement": "MEDIUM"},
        consequents={"mutation": "MEDIUM", "exploration": "MEDIUM"}
    ),
    # Additional complementary rules to guarantee smooth coverage across edge scenarios
    FuzzyRule(
        rule_id="R8",
        description="IF diversity is HIGH AND improvement is LOW THEN mutation is MEDIUM AND exploration is LOW",
        antecedents={"diversity": "HIGH", "improvement": "LOW"},
        consequents={"mutation": "MEDIUM", "exploration": "LOW"}
    ),
    FuzzyRule(
        rule_id="R9",
        description="IF disruption severity is LOW AND diversity is LOW THEN mutation is MEDIUM AND exploration is MEDIUM",
        antecedents={"severity": "LOW", "diversity": "LOW"},
        consequents={"mutation": "MEDIUM", "exploration": "MEDIUM"}
    )
]
