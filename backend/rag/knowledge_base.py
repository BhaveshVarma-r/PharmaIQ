from backend.database.chroma_manager import add_documents, query_collection
import logging

logger = logging.getLogger(__name__)


def seed_knowledge_base():
    _seed_cold_chain_protocols()
    _seed_disease_patterns()
    _seed_regulatory_references()
    _seed_scheduling_patterns()
    _seed_cross_domain_patterns()
    _seed_expiry_clearance_patterns()
    logger.info("Knowledge base seeded successfully")


def _seed_cold_chain_protocols():
    docs = [
        "WHO Cold Chain Protocol for Vaccines: Vaccines must be stored at 2 to 8 degrees Celsius at all times. The Vaccine Vial Monitor VVM stage 1 inner square lighter than outer circle means usable. Stage 2 inner square matches outer circle means do not use. Stage 3 or 4 inner square darker means discard immediately. Freeze-sensitive vaccines DTP HepB Hib IPV PCV must never be frozen. Cold chain breach documentation must include time of breach duration temperature range and affected vaccines.",
        "CDSCO Cold Chain Compliance Requirements: All temperature-sensitive drugs must have documented temperature logs for every batch retained for 5 years minimum. Any cold chain breach must be reported to State Drug Control Authority within 48 hours. Compromised batches must be quarantined within 2 hours of confirmed breach identification. CDSCO Form 19 must be filed for any batch recall due to cold chain failure.",
        "Insulin Cold Chain Management: Unopened insulin vials 2 to 8 degrees valid until expiry. Opened insulin can be stored below 30 degrees for up to 28 days. Insulin must never be frozen as freezing permanently denatures the protein. Temperature excursion above 8 degrees for more than 4 hours requires quarantine and assessment.",
        "Biologic Drug Storage Protocols: Most biologics require 2 to 8 degrees Celsius. Freeze-thaw cycles irreversibly damage most biologics even if temperature recovers. A single freeze-thaw event constitutes grounds for quarantine regardless of duration.",
        "Cold Chain Breach Severity Classification: SPIKE temperature outside range less than 15 minutes returns to range log only. MINOR 0 to 2 degree deviation under 30 minutes log and monitor. MODERATE 2 to 5 degree deviation OR 30 to 120 minutes quarantine batch. CRITICAL above 5 degree deviation OR above 120 minutes immediate quarantine and CDSCO notification. For vaccines any deviation above 8 degrees is CRITICAL regardless of duration.",
    ]
    metadatas = [
        {"source": "WHO_cold_chain", "category": "vaccine_storage"},
        {"source": "CDSCO_guidelines", "category": "regulatory_compliance"},
        {"source": "insulin_guidelines", "category": "drug_storage"},
        {"source": "biologic_guidelines", "category": "drug_storage"},
        {"source": "breach_classification", "category": "operational_protocol"},
    ]
    ids = ["cold_chain_{}".format(i) for i in range(len(docs))]
    add_documents("cold_chain_protocols", docs, metadatas, ids)


def _seed_disease_patterns():
    docs = [
        "Dengue IDSP Pattern: Reporting lag 7 to 10 days from symptom cluster to P-report publication. Demand begins rising day 3 after IDSP report peaks at day 10 to 14. Primary SKUs Paracetamol 650mg NOT 500mg, Dengue NS1 Antigen Test Kit Rapid, Papaya Leaf Extract 1100mg, ORS Sachets, Platelet supplements. Demand multiplier 3x to 5x baseline. Geographic spread 15km radius Tier 1 cities 25km Tier 2 cities.",
        "Malaria IDSP Pattern: Reporting lag 5 to 7 days. Primary SKUs Artemether-Lumefantrine, Chloroquine 250mg, Malaria RDT Kit, Paracetamol 500mg, Primaquine. Demand multiplier 2x to 4x. Seasonal peak June to November.",
        "Influenza IDSP Pattern: Reporting lag 3 to 5 days. Demand rises day 2 peaks day 5 to 10. Primary SKUs Oseltamivir 75mg, Paracetamol, Cetirizine, Azithromycin, N95 Masks, Vitamin C. Demand multiplier 2x to 3.5x. Winter peak October to February.",
        "Cholera IDSP Pattern: Reporting lag 3 to 5 days. Demand spike begins day 1 to 2. Primary SKUs ORS Sachets, Zinc 20mg, Metronidazole, Norfloxacin, Electral Powder. Demand multiplier 4x to 8x highest of all diseases. Post-flood high risk.",
        "Typhoid IDSP Pattern: Reporting lag 7 to 12 days. Primary SKUs Cefixime 200mg, Azithromycin, ORS Sachets, Electral Powder, Paracetamol. Demand multiplier 2x to 3x. Increasing fluoroquinolone resistance means Cefixime demand increases during outbreaks.",
    ]
    metadatas = [
        {"disease": "dengue", "source": "IDSP_pattern_library"},
        {"disease": "malaria", "source": "IDSP_pattern_library"},
        {"disease": "influenza", "source": "IDSP_pattern_library"},
        {"disease": "cholera", "source": "IDSP_pattern_library"},
        {"disease": "typhoid", "source": "IDSP_pattern_library"},
    ]
    ids = ["disease_{}".format(i) for i in range(len(docs))]
    add_documents("disease_patterns", docs, metadatas, ids)


def _seed_regulatory_references():
    docs = [
        "Drugs and Cosmetics Act 1940 Schedule H: Schedule H drugs can only be sold on prescription of a Registered Medical Practitioner. A registered pharmacist must be physically present at time of dispensing Schedule H drugs. The prescription must be retained for a period of 2 years. Violation imprisonment up to 1 year or fine up to 1000 rupees or both for first offence. Subsequent violation imprisonment up to 2 years and fine.",
        "Drugs and Cosmetics Act 1940 Schedule H1: Schedule H1 is a subset with stricter controls including third and fourth generation cephalosporins carbapenems fluoroquinolones macrolides. Pharmacist must maintain separate register with patient details prescribing doctor details and drug dispensed details. Register must be preserved 3 years. Cannot be dispensed more than twice on same prescription.",
        "CDSCO Drug Recall Protocol: Class I defects may cause serious adverse health consequences or death, removal within 2 hours of notification. Class II may cause temporary adverse consequences, removal within 24 hours. Class III unlikely to cause adverse consequences, removal within 5 days. All recalled stock must be segregated labeled and returned to distributor with documentation.",
        "Pharmacy Staff Compliance Registered Pharmacist Requirements: Every retail pharmacy must have a registered pharmacist in attendance during business hours. One pharmacist can supervise only one pharmacy at a time. Absence of registered pharmacist means pharmacy must close immediately for prescription services. Pharmacy licence can be suspended for repeated violations.",
    ]
    metadatas = [
        {"source": "Drugs_Cosmetics_Act_1940", "section": "Schedule_H"},
        {"source": "Drugs_Cosmetics_Act_1940", "section": "Schedule_H1"},
        {"source": "CDSCO_recall_protocol", "section": "recall_classification"},
        {"source": "Drugs_Cosmetics_Act_1940", "section": "pharmacist_requirements"},
    ]
    ids = ["regulatory_{}".format(i) for i in range(len(docs))]
    add_documents("regulatory_references", docs, metadatas, ids)


def _seed_scheduling_patterns():
    docs = [
        "Pharmacy Footfall Patterns Tier 1 Cities: Morning peak 7 to 9 AM prescription rush. Afternoon trough 12 to 3 PM 20 to 30 percent of daily footfall. Evening peak 5 to 8 PM post-work window. Weekend morning peak shifts to 10 AM to 12 PM. Staffing formula base 2 staff plus 1 per 50 expected patients per hour during peak. Minimum 1 registered pharmacist at all times 2 during peak recommended.",
        "Seasonal Staffing Multipliers: Monsoon June to September OTC medications footfall plus 20 percent prescription plus 15 percent. Winter November to January respiratory medications plus 25 percent elderly patient traffic increases 30 percent. Festival season Diwali Holi general footfall plus 10 percent prescription minus 20 percent. Disease alert active apply PULSE footfall multiplier typically 1.3x to 1.8x.",
        "Schedule H Compliance Risk Windows: Highest risk periods for compliance gaps are early morning shift change 7 to 8 AM, lunch break overlap 1 to 2 PM, evening shift change 6 to 7 PM, store closing rush 30 minutes before close. Mitigation schedule shift overlaps of minimum 30 minutes at every transition. No pharmacist should leave until replacement has physically arrived.",
    ]
    metadatas = [
        {"source": "operational_data", "category": "footfall_patterns"},
        {"source": "operational_data", "category": "seasonal_multipliers"},
        {"source": "compliance_framework", "category": "schedule_h_risk"},
    ]
    ids = ["scheduling_{}".format(i) for i in range(len(docs))]
    add_documents("scheduling_patterns", docs, metadatas, ids)


def _seed_cross_domain_patterns():
    docs = [
        "Cross-Domain Pattern 1 Epidemic to Operations Cascade: Trigger PULSE detects outbreak ALERT or OUTBREAK level. SOMA must increase staffing at affected stores using footfall_multiplier_for_soma from PULSE. SOMA must verify cold chain capacity for vaccine surge. PULSE must check if epidemic SKUs overlap with near-expiry stock. SOMA staffing plan must use PULSE footfall_multiplier_for_soma field specifically.",
        "Cross-Domain Pattern 2 Cold Chain Failure to Procurement Cascade: Trigger SOMA detects CRITICAL cold chain breach. PULSE must calculate emergency replacement quantity within 30 minutes. PULSE must identify nearest stores within 30km with same SKU stock for patient continuity. All cross-domain actions must complete within 120 minutes of breach confirmation.",
        "Cross-Domain Pattern 3 Staff Shortage to Dispensing Risk Cascade: Trigger SOMA detects Schedule H compliance gap zero pharmacists in window. PULSE checks expected dispensing volume of Schedule H drugs during gap window. If high Schedule H volume expected escalate immediately to store manager. If gap above 4 hours escalate to Head of Operations.",
        "Cross-Domain Pattern 4 Expiry Spike to Procurement Optimisation: Trigger PULSE detects near-expiry volume above 20 percent of store inventory for any SKU category. Check if demand forecast was accurate if not adjust PULSE parameters. Check if cold chain drug and verify no cold chain breaches accelerated expiry. If multiple stores show same pattern it is systemic forecast failure escalate to Head of Procurement.",
    ]
    metadatas = [
        {"pattern": "epidemic_operations", "priority": "HIGH"},
        {"pattern": "cold_chain_procurement", "priority": "CRITICAL"},
        {"pattern": "staff_dispensing_risk", "priority": "HIGH"},
        {"pattern": "expiry_procurement", "priority": "MEDIUM"},
    ]
    ids = ["cross_domain_{}".format(i) for i in range(len(docs))]
    add_documents("cross_domain_patterns", docs, metadatas, ids)


def _seed_expiry_clearance_patterns():
    docs = [
        "Near-Expiry Clearance Successful Patterns: Inter-store transfer preferred no margin loss, minimum 15 days remaining shelf life post-transfer, maximum transfer distance 50km, success rate 78 percent when transferred above 45 days before expiry. Bulk institutional discount 25 to 40 percent for bulk purchase minimum 100 units tablets 20 units injectables. Markdown at store level up to 15 percent store manager authority above 15 percent Head of Operations authority, optimal window 45 to 60 days before expiry. Return to distributor most accept returns up to 3 months before expiry credit note for 70 to 80 percent of purchase price.",
    ]
    metadatas = [{"source": "operational_data", "category": "expiry_clearance"}]
    ids = ["expiry_clearance_0"]
    add_documents("expiry_clearance_patterns", docs, metadatas, ids)


def get_cold_chain_context(query, n=2):
    results = query_collection("cold_chain_protocols", query, n)
    return "\n\n".join([r["content"] for r in results]) or "No relevant cold chain protocols found."


def get_disease_context(disease_name, n=2):
    results = query_collection("disease_patterns", disease_name, n)
    return "\n\n".join([r["content"] for r in results]) or "No relevant disease patterns found."


def get_regulatory_context(query, n=2):
    results = query_collection("regulatory_references", query, n)
    return "\n\n".join([r["content"] for r in results]) or "No relevant regulatory references found."


def get_scheduling_context(query, n=2):
    results = query_collection("scheduling_patterns", query, n)
    return "\n\n".join([r["content"] for r in results]) or "No relevant scheduling patterns found."


def get_cross_domain_context(query, n=2):
    results = query_collection("cross_domain_patterns", query, n)
    return "\n\n".join([r["content"] for r in results]) or "No relevant cross-domain patterns found."


def get_expiry_context(query, n=2):
    results = query_collection("expiry_clearance_patterns", query, n)
    return "\n\n".join([r["content"] for r in results]) or "No relevant expiry clearance patterns found."