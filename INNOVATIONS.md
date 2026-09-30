# AdaptIQ-R — Track Innovations

## Overview

AdaptIQ-R contributes the following novel technical innovations at the intersection of computational intelligence, evolutionary computation, and real-time logistics optimisation.

---

## Innovation 1: Online Mamdani FIS for GA Hyperparameter Adaptation in VRP

**What it is**: A complete three-input, two-output Mamdani Fuzzy Inference System implemented entirely in pure Python (no scikit-fuzzy or any fuzzy library) that adapts Genetic Algorithm mutation rate and exploration level in real time on every generation.

**Why it is novel**:
- Classical adaptive GAs use self-adaptive strategies (e.g., 1/5 rule, CMA-ES) or deterministic schedules. These are either single-parameter or require gradient information.
- Prior fuzzy-adaptive GAs in the literature (e.g., Lee & Takagi 1993, Herrera & Lozano 2003) apply fuzzy adaptation to static benchmark functions (De Jong suite, Rastrigin).
- **AdaptIQ-R applies Mamdani FIS adaptation to online VRP disruption recovery** — the first such coupling found in the open literature for dynamic logistics routing.

**Key components**:
- 3 inputs: population diversity, fitness improvement rate, disruption severity
- 2 outputs: mutation rate ∈ [0.05, 0.45], exploration level ∈ [0.10, 0.90]
- 9 auditable fuzzy rules with min-implication, max-aggregation, centroid defuzzification
- All implemented from mathematical first principles

---

## Innovation 2: Disruption Severity as a Real-Time Fuzzy Input Signal

**What it is**: A composite severity signal combining four heterogeneous disruption types (road blocks, traffic surge, priority change, vehicle failure) into a single scalar ∈ [0, 1] via weighted combination.

**Why it is novel**: Existing adaptive GAs treat the fitness landscape as a black-box function — they have no semantic knowledge of *why* it changed. AdaptIQ-R uses domain-specific disruption telemetry as a direct FIS input, enabling *proactive* adaptation before the fitness degradation propagates through the population.

**Formula**:
$$S = 0.40 \cdot \frac{|\text{Edges}_{\text{blocked}}|}{|\text{Edges}|} + 0.30 \cdot \frac{\Delta\text{Traffic}}{\text{Traffic}_{\max}} + 0.15 \cdot \frac{\Delta\text{Priority}}{\text{Priority}_{\max}} + 0.15 \cdot \frac{\Delta\text{Capacity}}{\text{Capacity}_0}$$

---

## Innovation 3: Exploration-Scaled Tournament Selection Pressure

**What it is**: Tournament size dynamically varies with the fuzzy exploration level output:

$$k_{\text{tournament}} = \max\left(2, \left\lfloor 2 + 3 \cdot (1 - \text{exploration\_level}) \right\rfloor\right)$$

**Why it is novel**: Standard adaptive tournament selection uses fixed k or annealing schedules. Coupling selection pressure to the FIS exploration output creates a *coordinated* exploration-exploitation tradeoff — the fuzzy controller simultaneously tightens both mutation and selection pressure during exploitation, and loosens both during disruption recovery.

---

## Innovation 4: Adaptive Multi-Swap Mutation with Exploration Scaling

**What it is**: The number of simultaneous gene swaps in each mutation event scales with the fuzzy exploration level:

$$k_{\text{swaps}} = \max\left(1, \left\lfloor 1 + 3 \cdot \text{exploration\_level} \right\rfloor\right)$$

**Why it is novel**: Classical adaptive mutation operators adjust *probability* of mutation. AdaptIQ-R adjusts the *structural magnitude* — the number of position swaps per mutation event. This provides finer control over the search radius in permutation space without sacrificing the validity of the permutation encoding.

---

## Innovation 5: Infeasibility-Tolerant Multi-Objective Fitness with Euclidean Fallback

**What it is**: When a disruption severs road connectivity making a route segment unreachable, instead of rejecting the individual, AdaptIQ-R computes a penalised Euclidean fallback distance estimate, applies a large infeasibility penalty, and marks the route as infeasible — preserving the individual's genetic material for recombination.

**Why it is novel**: Most VRP formulations discard infeasible solutions entirely. Preserving them with a graded penalty maintains population diversity during severe disruption recovery, enabling the GA to gradually evolve back to feasibility rather than restarting from scratch.

---

## Innovation 6: Zero-Dependency Pure Python Mamdani FIS

**What it is**: All fuzzy membership functions (triangular, trapezoidal), fuzzification, implication, aggregation, and centroid defuzzification are implemented in approximately 200 lines of pure Python with no dependencies on numpy, scipy, or any fuzzy library.

**Why it matters**: 
- Full mathematical transparency — every computation is inspectable
- No dependency conflicts in research reproducibility
- Enables deployment in constrained environments
- Facilitates formal verification and theorem proving of the inference logic

---

## Comparison with Prior Work

| Feature | Herrera & Lozano (2003) | Liu et al. (2019) | **AdaptIQ-R** |
|:--------|:-----------------------|:------------------|:--------------|
| Problem domain | Static benchmark functions | Fixed-cost VRP | **Dynamic VRP with disruptions** |
| FIS type | Mamdani | Type-2 Fuzzy | **Mamdani (pure Python)** |
| Inputs to FIS | Diversity, convergence rate | Population variance | **Diversity + Improvement + Disruption Severity** |
| Adaptation target | Mutation probability only | Crossover rate | **Mutation rate + Exploration level + Selection pressure** |
| Disruption handling | Not applicable | Offline re-optimisation | **Online, generation-by-generation** |
| Library dependency | MATLAB Fuzzy Toolbox | scikit-fuzzy | **Zero — pure Python** |
