"""Behavioral simulator generating legitimate events based on World State."""

import random
from datetime import timedelta
from decimal import Decimal
from typing import List, Optional

from red_team.world.state import WorldState
from red_team.world.persona import PersonaParameters
from red_team.schemas.entities import Session, Transaction, Device, Relationship
from red_team.schemas.events import (
    Event, EventEnvelope, EventType,
    TransactionEventPayload, SessionEventPayload, DeviceEventPayload, RelationshipEventPayload
)


class BehavioralSimulator:
    """Simulates stateful, legitimate payment behavior."""

    def __init__(self, random_seed: int, personas: List[PersonaParameters]):
        self.rng = random.Random(random_seed)
        self.personas = {p.segment_id: p for p in personas}

    def generate_next_event(self, state: WorldState) -> Optional[Event]:
        """Generate the next legitimate event for a random customer.
        
        Updates the WorldState directly if applicable (e.g. balance changes).
        """
        if not state.customers:
            return None
            
        # 1. Pick a random customer
        customer_id = self.rng.choice(list(state.customers.keys()))
        customer = state.customers[customer_id]
        persona = self.personas[customer.behavioral_segment]
        
        # 2. Advance time a small logical step (simulates chronological generation)
        state.advance_time(self.rng.randint(60, 3600))
        
        # 3. Drift: Occasional new device or relationship (1% chance)
        if self.rng.random() < 0.01:
            return self._generate_drift_event(state, customer_id)
            
        # 4. Standard Behavior: Session + Transaction
        # Are they in an active session?
        if customer_id not in state.active_sessions:
            return self._generate_session_login(state, customer_id)
        
        session = state.active_sessions[customer_id]
        
        # If in session, maybe transact or logout
        action_choice = self.rng.choices(["transact", "logout"], weights=[0.8, 0.2])[0]
        
        if action_choice == "logout":
            return self._generate_session_logout(state, customer_id)
        else:
            return self._generate_transaction(state, customer_id, persona)

    def _generate_session_login(self, state: WorldState, customer_id: str) -> Event:
        # Pick a device if they have one mapped, else create a generic one mapping
        devices = state.customer_devices.get(customer_id)
        device_id = None
        if devices:
            device_id = self.rng.choice(devices)
            
        session = Session(
            customer_id=customer_id,
            device_id=device_id,
            ip_address="192.168.1.1",
            start_time=state.current_time,
            auth_method="password",
            auth_success=True,
        )
        state.active_sessions[customer_id] = session
        
        envelope = EventEnvelope(
            timestamp=state.current_time,
            event_type=EventType.SESSION_LOGIN,
            customer_id=customer_id,
            session_id=session.session_id,
        )
        payload = SessionEventPayload(session=session, action="login", login_attempt_count=1)
        return Event(envelope=envelope, payload=payload)

    def _generate_session_logout(self, state: WorldState, customer_id: str) -> Event:
        session = state.active_sessions.pop(customer_id)
        session.end_time = state.current_time
        
        envelope = EventEnvelope(
            timestamp=state.current_time,
            event_type=EventType.SESSION_LOGOUT,
            customer_id=customer_id,
            session_id=session.session_id,
        )
        payload = SessionEventPayload(session=session, action="logout", login_attempt_count=1)
        return Event(envelope=envelope, payload=payload)

    def _generate_transaction(self, state: WorldState, customer_id: str, persona: PersonaParameters) -> Optional[Event]:
        # Find accounts
        customer_accts = [a for a in state.accounts.values() if a.customer_id == customer_id]
        if not customer_accts:
            return None
        account = self.rng.choice(customer_accts)
        
        session = state.active_sessions[customer_id]
        
        # Decide type (purchase vs transfer)
        tx_type = self.rng.choices(["purchase", "transfer"], weights=[0.8, 0.2])[0]
        
        amount_val = self.rng.uniform(persona.typical_amount_range[0], persona.typical_amount_range[1])
        amount = Decimal(str(round(amount_val, 2)))
        
        merchant_id = None
        beneficiary_id = None
        
        if tx_type == "purchase" and state.merchants:
            merchant_id = self.rng.choice(list(state.merchants.keys()))
        elif tx_type == "transfer" and state.beneficiaries:
            # Pick from related beneficiaries if possible
            rels = [r for r in state.relationships.values() 
                    if r.source_entity_id == customer_id and r.target_entity_type == "beneficiary"]
            if rels:
                beneficiary_id = self.rng.choice(rels).target_entity_id
            else:
                beneficiary_id = self.rng.choice(list(state.beneficiaries.keys()))
        else:
            return None
            
        pre_balance = account.balance
        
        # Check balance
        if account.account_type in ("checking", "savings", "business"):
            if account.balance < amount:
                # Top up balance (simulate legitimate deposit)
                account.balance += amount * 2
                pre_balance = account.balance
                
        account.balance -= amount
        
        tx = Transaction(
            account_id=account.account_id,
            session_id=session.session_id,
            amount=amount,
            currency="USD",
            transaction_type=tx_type,
            merchant_id=merchant_id,
            beneficiary_id=beneficiary_id,
            channel="mobile",
            timestamp=state.current_time,
        )
        
        envelope = EventEnvelope(
            timestamp=state.current_time,
            event_type=EventType.TRANSACTION,
            customer_id=customer_id,
            account_id=account.account_id,
            session_id=session.session_id,
        )
        payload = TransactionEventPayload(transaction=tx, pre_balance=pre_balance, post_balance=account.balance)
        return Event(envelope=envelope, payload=payload)

    def _generate_drift_event(self, state: WorldState, customer_id: str) -> Event:
        # Register a new device to simulate drift
        device = Device(
            device_type="mobile",
            fingerprint=f"NEW_FINGERPRINT_{self.rng.randint(1000,9999)}",
            first_seen=state.current_time,
            last_seen=state.current_time,
            is_trusted=False
        )
        state.devices[device.device_id] = device
        
        if customer_id not in state.customer_devices:
            state.customer_devices[customer_id] = []
        state.customer_devices[customer_id].append(device.device_id)
        
        envelope = EventEnvelope(
            timestamp=state.current_time,
            event_type=EventType.DEVICE_REGISTRATION,
            customer_id=customer_id,
        )
        payload = DeviceEventPayload(device=device, action="register")
        return Event(envelope=envelope, payload=payload)
