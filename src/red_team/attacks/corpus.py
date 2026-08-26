"""Corpus Generation Module.

Handles batch generation of synthetic attack traces using the StatefulSimulator
and validates them using the RealismValidator.
"""

import random
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from red_team.world.state import WorldState
from red_team.attacks.ato_signature import get_ato_signature
from red_team.attacks.simulator import StatefulSimulator, AttackPlan
from red_team.schemas.observable import ObservableAttackTrace
from red_team.schemas.ground_truth import AttackGroundTruth
from red_team.validation.realism import RealismReport, validate_attack_realism


class AttackRecord(BaseModel):
    """Internal storage format coupling trace, ground truth, and validation."""
    observable_trace: ObservableAttackTrace
    ground_truth: AttackGroundTruth
    validation_metadata: RealismReport


class GenerationStatistics(BaseModel):
    """Statistics for a generation run."""
    attempted: int
    accepted: int
    rejected: int
    acceptance_rate: float
    
    # Path diversity
    unique_phase_sequences: int
    unique_entry_paths: int
    average_phases_per_attack: float
    
    # Event diversity
    average_events_per_attack: float
    min_events: int
    max_events: int
    event_type_distribution: Dict[str, int]
    
    # Difficulty
    difficulty_distribution: Dict[str, int]
    
    # Customer diversity
    unique_customers_attacked: int
    
    # Realism distribution
    realism_distribution: Dict[str, float]  # just simple averages or counts for now
    not_available_metric_count: int


class CorpusGenerationResult(BaseModel):
    """Result of a batch generation run."""
    accepted_traces: List[AttackRecord]
    rejected_attempts: List[Dict[str, Any]]
    generation_statistics: GenerationStatistics


def generate_attack_corpus(
    world_state: WorldState,
    target_count: int = 100,
    master_seed: int = 42,
    max_attempts: int = 500
) -> CorpusGenerationResult:
    """Generate a valid corpus of attacks."""
    
    rng = random.Random(master_seed)
    signature = get_ato_signature()
    
    accepted = []
    rejected = []
    
    customer_ids = list(world_state.customers.keys())
    if not customer_ids:
        raise ValueError("World state has no customers to attack.")
        
    difficulties = ["easy", "medium", "hard", "advanced"]
    entry_paths = ["RECONNAISSANCE", "ACCOUNT_ACCESS"]
    
    attempt = 0
    while len(accepted) < target_count and attempt < max_attempts:
        attempt += 1
        child_seed = rng.getrandbits(32)
        
        # Select customer and variations deterministically using rng
        customer_id = rng.choice(customer_ids)
        diff = rng.choice(difficulties)
        entry = rng.choice(entry_paths)
        
        plan = AttackPlan(
            attack_family="ACCOUNT_TAKEOVER",
            difficulty=diff,
            entry_state=entry,
            max_phases=rng.randint(3, 8)
        )
        
        sim = StatefulSimulator(world_state, signature, seed=child_seed)
        try:
            trace, gt = sim.generate_attack(plan, customer_id)
        except Exception as e:
            rejected.append({
                "attempt_id": attempt,
                "seed": child_seed,
                "failure_category": "simulation_error",
                "failure_reason": str(e)
            })
            continue
            
        report = validate_attack_realism(trace, gt, signature, world_state)
        
        # Gate: Structural and Constraint must PASS
        if report.status == "ACCEPTED" and report.structural.passed and report.constraint.passed:
            record = AttackRecord(
                observable_trace=trace,
                ground_truth=gt,
                validation_metadata=report
            )
            accepted.append(record)
        else:
            rejected.append({
                "attempt_id": attempt,
                "seed": child_seed,
                "failure_category": "validation_rejection",
                "failure_reason": "; ".join(report.failures)
            })
            
    # Calculate statistics
    stats = _calculate_statistics(accepted, rejected, attempt)
    
    return CorpusGenerationResult(
        accepted_traces=accepted,
        rejected_attempts=rejected,
        generation_statistics=stats
    )


def _calculate_statistics(accepted: List[AttackRecord], rejected: List[Dict[str, Any]], attempts: int) -> GenerationStatistics:
    if not accepted:
        return GenerationStatistics(
            attempted=attempts, accepted=0, rejected=len(rejected), acceptance_rate=0.0,
            unique_phase_sequences=0, unique_entry_paths=0, average_phases_per_attack=0.0,
            average_events_per_attack=0.0, min_events=0, max_events=0, event_type_distribution={},
            difficulty_distribution={}, unique_customers_attacked=0,
            realism_distribution={}, not_available_metric_count=0
        )
        
    # Paths
    phase_seqs = set()
    entry_paths = set()
    total_phases = 0
    
    # Events
    total_events = 0
    min_ev = float('inf')
    max_ev = 0
    evt_types = {}
    
    # Diff
    diffs = {"easy": 0, "medium": 0, "hard": 0, "advanced": 0}
    
    # Customer
    customers = set()
    
    # Realism
    na_count = 0
    
    for rec in accepted:
        # Paths
        seq = tuple(p.phase for p in rec.ground_truth.phases_executed)
        phase_seqs.add(seq)
        if seq:
            entry_paths.add(seq[0])
        total_phases += len(seq)
        
        # Events
        num_ev = len(rec.observable_trace.events)
        total_events += num_ev
        if num_ev < min_ev: min_ev = num_ev
        if num_ev > max_ev: max_ev = num_ev
        
        for e in rec.observable_trace.events:
            evt_types[e.event_type] = evt_types.get(e.event_type, 0) + 1
            
        # Diff
        diffs[rec.ground_truth.attack_difficulty] = diffs.get(rec.ground_truth.attack_difficulty, 0) + 1
        
        # Customer
        customers.add(rec.observable_trace.customer_id)
        
        # Realism
        if rec.validation_metadata.overall_realism_score == "NOT_AVAILABLE":
            na_count += 1
            
    return GenerationStatistics(
        attempted=attempts,
        accepted=len(accepted),
        rejected=len(rejected),
        acceptance_rate=len(accepted) / attempts if attempts > 0 else 0.0,
        unique_phase_sequences=len(phase_seqs),
        unique_entry_paths=len(entry_paths),
        average_phases_per_attack=total_phases / len(accepted),
        average_events_per_attack=total_events / len(accepted),
        min_events=min_ev,
        max_events=max_ev,
        event_type_distribution=evt_types,
        difficulty_distribution=diffs,
        unique_customers_attacked=len(customers),
        realism_distribution={"average_score": 1.0}, # Dummy for now
        not_available_metric_count=na_count
    )
