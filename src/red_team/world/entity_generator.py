"""Entity generator for the Normal World.

Uses Personas to generate structurally valid Stage 2 entities.
"""

import random
from datetime import datetime, timedelta
from typing import List, Tuple
from decimal import Decimal

from red_team.schemas.entities import (
    Customer,
    Account,
    Device,
    Merchant,
    Beneficiary,
    Relationship,
)
from red_team.world.persona import PersonaParameters


class EntityGenerator:
    """Generates the initial synthetic population."""

    def __init__(self, random_seed: int, start_time: datetime):
        self.rng = random.Random(random_seed)
        self.start_time = start_time

    def _random_date_before(self, dt: datetime, days_range: int = 365) -> datetime:
        days = self.rng.randint(1, days_range)
        return dt - timedelta(days=days)

    def generate_population(
        self,
        personas: List[PersonaParameters],
        num_customers: int,
        num_merchants: int,
        num_beneficiaries: int,
    ) -> Tuple[List[Customer], List[Account], List[Device], List[Merchant], List[Beneficiary], List[Relationship]]:
        
        customers = []
        accounts = []
        devices = []
        merchants = []
        beneficiaries = []
        relationships = []

        # Generate Merchants
        for i in range(num_merchants):
            m = Merchant(
                name=f"Merchant_{i}",
                mcc_code=f"{self.rng.randint(1000, 9999)}",
                category="Retail",
                country="US",
                risk_level="low",
            )
            merchants.append(m)

        # Generate Beneficiaries
        for i in range(num_beneficiaries):
            b = Beneficiary(
                name=f"Beneficiary_{i}",
                account_reference=f"ACC-REF-{self.rng.randint(10000, 99999)}",
                bank_code="BANK123",
                created_date=self._random_date_before(self.start_time, 365),
                relationship_type=self.rng.choice(["personal", "business", "utility"]),
            )
            beneficiaries.append(b)

        # Generate Customers, Accounts, Devices, Relationships
        for i in range(num_customers):
            persona = self.rng.choice(personas)
            reg_date = self._random_date_before(self.start_time)
            
            c = Customer(
                name=f"Customer_{i}",
                registration_date=reg_date,
                behavioral_segment=persona.segment_id,
                country="US",
            )
            customers.append(c)

            # Generate Accounts (1-2 per customer)
            num_accts = self.rng.randint(1, 2)
            for _ in range(num_accts):
                a = Account(
                    customer_id=c.customer_id,
                    account_type=self.rng.choice(["checking", "savings", "credit"]),
                    currency="USD",
                    opened_date=self._random_date_before(self.start_time, 30),
                    balance=Decimal(str(self.rng.randint(1000, 50000))),
                )
                accounts.append(a)
                
            # Generate Devices
            num_devs = 1 if persona.device_count_tendency == "single" else self.rng.randint(2, 3)
            for _ in range(num_devs):
                first = self._random_date_before(self.start_time, 60)
                last = first + timedelta(days=self.rng.randint(0, 50))
                if last > self.start_time:
                    last = self.start_time
                    
                d = Device(
                    device_type=self.rng.choice(["mobile", "desktop", "tablet"]),
                    os="SimOS",
                    browser="SimBrowser",
                    fingerprint=f"FINGERPRINT_{self.rng.randint(1000,9999)}",
                    first_seen=first,
                    last_seen=last,
                    is_trusted=True,
                )
                devices.append(d)
                
            # Connect to Beneficiaries
            num_bens = self.rng.randint(*persona.beneficiary_count_range)
            selected_bens = self.rng.sample(beneficiaries, min(num_bens, len(beneficiaries)))
            
            for b in selected_bens:
                rel = Relationship(
                    source_entity_type="customer",
                    source_entity_id=c.customer_id,
                    target_entity_type="beneficiary",
                    target_entity_id=b.beneficiary_id,
                    relationship_type="transacts_with",
                    established_date=self._random_date_before(self.start_time, 60),
                    strength_score=0.5,
                )
                relationships.append(rel)

        return customers, accounts, devices, merchants, beneficiaries, relationships
