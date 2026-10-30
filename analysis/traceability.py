"""Traceability Graph and Matrix Engine for Q-Pack.

Constructs a bipartite/multipartite NetworkX graph linking Requirements, Components,
Assumptions, Models, Results, and Validation Evidence. Generates full compliance matrices
and Design Dossiers.
"""

from __future__ import annotations
from typing import Dict, List, Any, Optional
import networkx as nx
import pandas as pd

from core.schemas import EvaluationResult, PackDesign, RequirementStatus
from core.data_loader import load_requirements


def build_traceability_graph(result: Optional[EvaluationResult] = None) -> nx.DiGraph:
    """Build directed traceability graph connecting all system engineering entities."""
    g = nx.DiGraph()
    reqs = load_requirements()

    # 1. Add Requirement Nodes
    for req_id, req in reqs.items():
        g.add_node(
            req_id,
            node_type="Requirement",
            title=req_id,
            description=req.text,
            rationale=req.rationale,
            target=f"{req.target_value} {req.unit}",
        )

    # 2. Add Component Nodes
    components = {
        "COMP_CELL": ("Component", "Battery Cells", "Electrochemical energy storage unit"),
        "COMP_BMS": ("Component", "Battery Management System", "Protection, sensing, and balancing"),
        "COMP_COOLING": ("Component", "Thermal Dissipation System", "Convection/conduction hardware"),
        "COMP_BUSBAR": ("Component", "Interconnect Busbars", "High-conductivity inter-cell links"),
        "COMP_CASE": ("Component", "Structural Enclosure", "Mechanical crashworthiness and IP sealing"),
    }
    for comp_id, (n_type, title, desc) in components.items():
        g.add_node(comp_id, node_type=n_type, title=title, description=desc)

    # 3. Add Assumption Nodes
    assumptions = {
        "A-01": "Busbar resistance 0.15 mOhm/cell",
        "A-02": "Empirical OCV(SoC) interpolation curves",
        "A-03": "Inverter DC efficiency 95%",
        "A-04": "Cell specific heat capacity 950 J/(kg*K)",
        "A-05": "Cooling heat transfer coefficients h_eff",
        "A-06": "2D Thermal spatial gradient factor 0.25",
        "A-07": "CV charge phase exponential tail tau=18min",
        "A-08": "Thermal derating slope above 45 C",
        "A-09": "Enclosure mass fraction 18%",
        "A-10": "Enclosure cost $14/kg",
        "A-11": "Volumetric packing efficiency 72%",
        "A-12": "Arrhenius degradation activation energy 4500 K",
        "A-13": "Cell capacity manufacturing spread sigma=2%",
        "A-14": "Cell resistance manufacturing spread sigma=8%",
        "A-15": "Weakest series group discharge cutoff",
    }
    for a_id, desc in assumptions.items():
        g.add_node(a_id, node_type="Assumption", title=a_id, description=desc)

    # 4. Add Model Nodes
    models = {
        "MOD_ELEC": ("Model", "electrical.py", "Terminal sag, OCV, pack resistance"),
        "MOD_THERM": ("Model", "thermal.py", "Lumped ODE solve_ivp & 2D conduction"),
        "MOD_MECH": ("Model", "mechanical.py", "Pack mass, envelope, and packing density"),
        "MOD_CHG": ("Model", "charging.py", "CC-CV time-domain charge integration"),
        "MOD_COST": ("Model", "cost.py", "Itemized bottom-up BOM breakdown"),
        "MOD_AGE": ("Model", "ageing.py", "Semi-empirical cycle life surrogate"),
        "MOD_VAR": ("Model", "variation.py", "Monte Carlo weakest-group propagation"),
    }
    for mod_id, (n_type, title, desc) in models.items():
        g.add_node(mod_id, node_type=n_type, title=title, description=desc)

    # 5. Add Evidence Nodes (Tests and Validation)
    evidence = {
        "EVI_TEST_ELEC": ("Evidence", "test_electrical.py", "13S2P hand calculation & sag validation"),
        "EVI_TEST_THERM": ("Evidence", "test_thermal.py", "Cooling monotonicity & spatial gradient check"),
        "EVI_TEST_MECH": ("Evidence", "test_mechanical_cost.py", "Mass/volume formulas & BOM itemization"),
        "EVI_TEST_CHG": ("Evidence", "test_charging_ageing.py", "Thermal derating activation & Arrhenius trend"),
        "EVI_TEST_VAR": ("Evidence", "test_variation.py", "P5/P50/P95 quantile verification"),
        "EVI_TEST_DS": ("Evidence", "test_datasheet_crosscheck.py", "Single cell 0.2C discharge comparison"),
    }
    for evi_id, (n_type, title, desc) in evidence.items():
        g.add_node(evi_id, node_type=n_type, title=title, description=desc)

    # 6. Add Edges (Relationship Connections)
    # Requirement -> Component / Model
    edges = [
        ("R-01", "MOD_ELEC", "verified_by"),
        ("R-02", "MOD_ELEC", "verified_by"),
        ("R-03", "MOD_ELEC", "verified_by"),
        ("R-04", "MOD_ELEC", "verified_by"),
        ("R-05", "MOD_THERM", "verified_by"),
        ("R-06", "MOD_CHG", "verified_by"),
        ("R-07", "MOD_MECH", "verified_by"),
        ("R-08", "MOD_COST", "verified_by"),
        ("R-09", "MOD_AGE", "verified_by"),
        ("R-10", "MOD_ELEC", "verified_by"),
        ("R-11", "COMP_BMS", "satisfied_by"),
        ("R-12", "COMP_BMS", "satisfied_by"),

        # Models -> Components
        ("MOD_ELEC", "COMP_CELL", "models"),
        ("MOD_ELEC", "COMP_BUSBAR", "models"),
        ("MOD_THERM", "COMP_COOLING", "models"),
        ("MOD_MECH", "COMP_CASE", "models"),
        ("MOD_COST", "COMP_BMS", "models"),

        # Models -> Assumptions
        ("MOD_ELEC", "A-01", "uses_assumption"),
        ("MOD_ELEC", "A-02", "uses_assumption"),
        ("MOD_ELEC", "A-03", "uses_assumption"),
        ("MOD_THERM", "A-04", "uses_assumption"),
        ("MOD_THERM", "A-05", "uses_assumption"),
        ("MOD_THERM", "A-06", "uses_assumption"),
        ("MOD_CHG", "A-07", "uses_assumption"),
        ("MOD_CHG", "A-08", "uses_assumption"),
        ("MOD_MECH", "A-09", "uses_assumption"),
        ("MOD_COST", "A-10", "uses_assumption"),
        ("MOD_MECH", "A-11", "uses_assumption"),
        ("MOD_AGE", "A-12", "uses_assumption"),
        ("MOD_VAR", "A-13", "uses_assumption"),
        ("MOD_VAR", "A-14", "uses_assumption"),
        ("MOD_VAR", "A-15", "uses_assumption"),

        # Models -> Evidence
        ("MOD_ELEC", "EVI_TEST_ELEC", "validated_by"),
        ("MOD_ELEC", "EVI_TEST_DS", "validated_by"),
        ("MOD_THERM", "EVI_TEST_THERM", "validated_by"),
        ("MOD_MECH", "EVI_TEST_MECH", "validated_by"),
        ("MOD_CHG", "EVI_TEST_CHG", "validated_by"),
        ("MOD_AGE", "EVI_TEST_CHG", "validated_by"),
        ("MOD_VAR", "EVI_TEST_VAR", "validated_by"),
    ]

    for src, dst, rel in edges:
        g.add_edge(src, dst, relation=rel)

    return g


def generate_traceability_matrix(result: Optional[EvaluationResult] = None) -> pd.DataFrame:
    """Generate requirement-to-evidence compliance table."""
    reqs = load_requirements()
    rows = []

    for req_id, req in sorted(reqs.items()):
        status = result.requirements.get(req_id) if result else None
        rows.append({
            "Requirement ID": req_id,
            "Requirement Description": req.text,
            "Target Value": f"{req.target_value} {req.unit}",
            "Actual Value": f"{status.actual_value:.1f} {status.unit}" if status else "N/A",
            "Margin": f"{status.margin:+.1f} {status.unit}" if status else "N/A",
            "Compliance Status": ("PASS" if status.passed else "FAIL") if status else "Pending",
            "Verification Method": req.verification_method,
            "Linked Subsystems": "Electrical" if req_id in ["R-01", "R-02", "R-03", "R-04", "R-10"] else (
                "Thermal" if req_id == "R-05" else (
                    "Charging" if req_id == "R-06" else (
                        "Mechanical/BOM" if req_id in ["R-07", "R-08"] else (
                            "Ageing" if req_id == "R-09" else "BMS / Sensing"
                        )
                    )
                )
            ),
        })

    return pd.DataFrame(rows)


def generate_design_dossier(result: EvaluationResult) -> Dict[str, Any]:
    """Generate a comprehensive Design Dossier for a candidate pack design."""
    matrix_df = generate_traceability_matrix(result)

    # Risk analysis based on margins and findings
    risks = []
    for f in result.findings:
        risks.append({
            "Risk Item": f.title,
            "Severity": f.severity.upper(),
            "Impact": f.explanation,
            "Mitigation Strategy": f.suggested_fix,
        })

    # If no findings, record clean status
    if not risks:
        risks.append({
            "Risk Item": "Nominal Design Margins",
            "Severity": "LOW",
            "Impact": "All design parameters within safe bounds",
            "Mitigation Strategy": "Proceed to prototype hardware verification",
        })

    return {
        "design_name": result.design.name,
        "cell_id": result.design.cell_id,
        "configuration": f"{result.design.ns}S {result.design.np}P ({result.design.cooling.value}, {result.design.bms_tier.value})",
        "compliance_matrix": matrix_df.to_dict(orient="records"),
        "risks": risks,
        "limitations": [
            "Thermal model assumes lumped convective boundary; full 3D CFD required for localized stagnation zones.",
            "Cycle life derived from empirical Arrhenius surrogate; cell calendar ageing not modeled.",
            "Drive cycle is synthetic urban profile; dynamic road grade and regenerative braking excluded.",
        ],
        "recommended_next_experiment": "Construct 1S4P module test bench with embedded thermistors under 6 kW pulse profile to validate cell-to-cell gradient.",
    }

