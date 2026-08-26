"""Stateful ATO Attack Simulator.

Executes a structured attack plan against a legitimate customer's world state,
following the constrained state graph of an Attack Signature, producing
a strictly isolated ObservableAttackTrace and AttackGroundTruth pair.
"""

import uuid
import random
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Literal, Any
from pydantic import BaseModel, Field

from red_team.world.state import WorldState
from red_team.attacks.signature_library import AttackSignature, Observability
from red_team.schemas.events import (
    Event, EventEnvelope, EventType,
    Session, Device, Beneficiary,
    Transaction, Relationship,
    SessionEventPayload, DeviceEventPayload,
    BeneficiaryEventPayload, TransactionEventPayload,
    AccountContextEventPayload, RelationshipEventPayload
)
from red_team.schemas.observable import ObservableAttackTrace, extract_observable
from red_team.schemas.ground_truth import (
    AttackGroundTruth, AttackPhaseRecord,
    GenerationMetadata, PlannerMetadata, EvaluationMetadata
)


class AttackPlan(BaseModel):
    """Structured instruction for the Simulator."""
    attack_family: str
    entry_state: Optional[str] = None
    difficulty: Literal["easy", "medium", "hard", "advanced"]
    variation_settings: Dict[str, str] = Field(default_factory=dict)
    target_signal_intensity: str = "MEDIUM"
    affected_entity_preferences: List[str] = Field(default_factory=list)
    max_phases: int = 50
    max_events: int = 100
    max_simulation_duration_minutes: int = 1440


class StatefulSimulator:
    def __init__(self, state: WorldState, signature: AttackSignature, seed: int):
        self.state = state
        self.signature = signature
        self.seed = seed
        self.rng = random.Random(seed)
        
        self.generated_events: List[Event] = []
        self.phase_records: List[AttackPhaseRecord] = []
        
    def _generate_event_id(self) -> str:
        return str(uuid.UUID(int=self.rng.getrandbits(128)))

    def generate_attack(
        self, plan: AttackPlan, customer_id: str
    ) -> Tuple[ObservableAttackTrace, AttackGroundTruth]:
        """Execute the stateful simulation."""
        
        if customer_id not in self.state.customers:
            raise ValueError(f"Customer {customer_id} not found in WorldState")
            
        attack_id = f"atk-{self._generate_event_id()[:8]}"
        
        # 1. Determine entry state
        current_state_name = plan.entry_state
        if not current_state_name:
            current_state_name = self.rng.choice(self.signature.entry_states)
            
        phases_executed = 0
        events_generated = 0
        start_time = self.state.current_time
        
        # Current active components specific to this attacker session
        attacker_session: Optional[Session] = None
        attacker_device: Optional[Device] = None
        attacker_beneficiary: Optional[Beneficiary] = None
        
        while current_state_name != "END":
            # Safety limits
            if phases_executed >= plan.max_phases:
                break
            if events_generated >= plan.max_events:
                break
            if (self.state.current_time - start_time).total_seconds() / 60 > plan.max_simulation_duration_minutes:
                break
                
            phases_executed += 1
            attack_state = self.signature.states[current_state_name]
            
            phase_start = self.state.current_time
            
            # 2. Generate Events for the phase
            # For this mock simulator, we statically map consequences to simple events
            for consequence in attack_state.observable_consequences:
                # Basic event synthesis
                self.state.advance_time(self.rng.randint(5, 60))  # Advance time slightly
                
                new_events = self._synthesize_events_for_consequence(
                    consequence, customer_id, attacker_device, attacker_session, attacker_beneficiary
                )
                
                for ev in new_events:
                    # Update references if they were created
                    payload = ev.payload
                    if isinstance(payload, DeviceEventPayload) and payload.action == "register":
                        attacker_device = payload.device
                    elif isinstance(payload, SessionEventPayload):
                        attacker_session = payload.session
                    elif isinstance(payload, BeneficiaryEventPayload) and payload.action == "add":
                        attacker_beneficiary = payload.beneficiary
                    
                    self.state.append_event(ev)  # Mutates world state graph
                    self.generated_events.append(ev)
                    events_generated += 1
            
            phase_end = self.state.current_time
            
            # 3. Transition Selection
            transitions = attack_state.transitions
            if not transitions:
                break
                
            # Sample weights
            weights = []
            for t in transitions:
                w = self.rng.uniform(t.min_weight, t.max_weight)
                weights.append(w)
                
            total_w = sum(weights)
            if total_w <= 0:
                break
                
            normalized = [w / total_w for w in weights]
            
            # Create phase record before transitioning
            r = self.rng.random()
            cumulative = 0.0
            next_state_name = "END"
            for t, p in zip(transitions, normalized):
                cumulative += p
                if r <= cumulative:
                    next_state_name = t.target_state
                    break
            
            # Determine if phase was optional (simplistic check: can access skip it?)
            was_optional = False
            
            self.phase_records.append(
                AttackPhaseRecord(
                    phase=current_state_name,
                    entered_at=phase_start,
                    exited_at=phase_end,
                    transition_to=next_state_name,
                    was_optional=was_optional
                )
            )
            
            current_state_name = next_state_name

        # Finalize
        if not self.generated_events:
            raise ValueError("Attack generated zero events")

        # Create Output Artifacts
        trace = extract_observable(self.generated_events, trace_id=attack_id)
        
        ground_truth = self._create_ground_truth(attack_id, plan)
        
        return trace, ground_truth
        
    def _synthesize_events_for_consequence(
        self, consequence, customer_id: str, 
        device: Optional[Device], session: Optional[Session], beneficiary: Optional[Beneficiary]
    ) -> List[Event]:
        """Synthesize specific valid events based on consequence description."""
        events = []
        
        # Recon / Access -> Session/Device
        if "device" in consequence.affected_entities or "session" in consequence.affected_entities:
            if device is None:
                device = Device(
                    device_id=self._generate_event_id(),
                    device_type="desktop",
                    fingerprint=f"atk_fp_{self.rng.randint(100,999)}",
                    first_seen=self.state.current_time,
                    last_seen=self.state.current_time,
                    is_trusted=False
                )
                self.state.devices[device.device_id] = device
                
                env = EventEnvelope(
                    event_id=self._generate_event_id(),
                    timestamp=self.state.current_time,
                    event_type=EventType.DEVICE_REGISTRATION,
                    customer_id=customer_id
                )
                events.append(Event(envelope=env, payload=DeviceEventPayload(device=device, action="register")))
                
            if session is None:
                session = Session(
                    session_id=self._generate_event_id(),
                    customer_id=customer_id,
                    device_id=device.device_id,
                    ip_address="203.0.113.5",
                    start_time=self.state.current_time,
                    auth_method="password",
                    auth_success=True
                )
                self.state.active_sessions[customer_id] = session
                
                env = EventEnvelope(
                    event_id=self._generate_event_id(),
                    timestamp=self.state.current_time,
                    event_type=EventType.SESSION_LOGIN,
                    customer_id=customer_id,
                    session_id=session.session_id,
                    account_id=list(self.state.accounts.keys())[0] if self.state.accounts else None
                )
                events.append(Event(envelope=env, payload=SessionEventPayload(session=session, login_attempt_count=1)))
                
        # Modification -> Beneficiary/Context
        elif "beneficiary" in consequence.affected_entities and not "transaction" in consequence.affected_entities:
            if beneficiary is None:
                beneficiary = Beneficiary(
                    beneficiary_id=self._generate_event_id(),
                    name="Mock Beneficiary",
                    account_reference="offshore_acct",
                    created_date=self.state.current_time,
                    relationship_type="other",
                    is_verified=False
                )
                self.state.beneficiaries[beneficiary.beneficiary_id] = beneficiary
                
                env = EventEnvelope(
                    event_id=self._generate_event_id(),
                    timestamp=self.state.current_time,
                    event_type=EventType.BENEFICIARY_ADDITION,
                    customer_id=customer_id
                )
                events.append(Event(envelope=env, payload=BeneficiaryEventPayload(beneficiary=beneficiary, action="add")))
                
        # Exploitation -> Transaction
        elif "transaction" in consequence.affected_entities:
            acct_id = None
            # Find a checking account
            for a_id, acct in self.state.accounts.items():
                if acct.account_type in ("checking", "savings"):
                    acct_id = a_id
                    break
            if not acct_id and self.state.accounts:
                acct_id = list(self.state.accounts.keys())[0]
                
            if acct_id:
                from decimal import Decimal
                acct = self.state.accounts[acct_id]
                amt = Decimal("500.00")
                pre_balance = acct.balance
                
                # Mock legitimate topup if insufficient
                if acct.balance < amt:
                    acct.balance += amt * 2
                    pre_balance = acct.balance
                    
                acct.balance -= amt
                
                tx = Transaction(
                    account_id=acct_id,
                    session_id=session.session_id if session else None,
                    amount=amt,
                    currency="USD",
                    transaction_type="transfer" if beneficiary else "purchase",
                    beneficiary_id=beneficiary.beneficiary_id if beneficiary else None,
                    merchant_id=None if beneficiary else f"merch-{self._generate_event_id()[:8]}",
                    timestamp=self.state.current_time,
                    channel="online"
                )
                
                env = EventEnvelope(
                    event_id=self._generate_event_id(),
                    timestamp=self.state.current_time,
                    event_type=EventType.TRANSACTION,
                    customer_id=customer_id,
                    account_id=acct_id,
                    session_id=session.session_id if session else None
                )
                events.append(Event(envelope=env, payload=TransactionEventPayload(
                    transaction=tx, pre_balance=pre_balance, post_balance=acct.balance
                )))
                
        return events

    def _create_ground_truth(self, attack_id: str, plan: AttackPlan) -> AttackGroundTruth:
        conf_hash = hashlib.sha256(str(self.seed).encode()).hexdigest()[:8]
        
        gen_meta = GenerationMetadata(
            random_seed=self.seed,
            generator_version="1.0",
            signature_version=self.signature.version,
            provenance_registry_version="1.0",
            configuration_hash=conf_hash,
            generated_at=datetime.now(timezone.utc)
        )
        
        plan_meta = PlannerMetadata(
            planner_type="mock",
            plan_json=plan.model_dump(),
        )
        
        eval_meta = EvaluationMetadata(
            structural_valid=True,
        )
        
        return AttackGroundTruth(
            attack_id=attack_id,
            attack_family=self.signature.attack_family,
            attack_difficulty=plan.difficulty,
            hidden_objective="extract_funds",
            phases_executed=self.phase_records,
            linked_event_ids=[e.envelope.event_id for e in self.generated_events],
            generation_metadata=gen_meta,
            planner_metadata=plan_meta,
            evaluation_metadata=eval_meta
        )
