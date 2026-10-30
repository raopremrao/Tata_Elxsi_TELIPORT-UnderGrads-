"""Datasheet Cross-Check Validation Tests (Milestone M2).

Verifies that simulated single-cell and pack discharge under standard datasheet
test currents replicates official datasheet capacity and thermal specifications.
"""

import numpy as np
from core.data_loader import load_cells
from core.schemas import PackDesign, CoolingType
from models.electrical import simulate_drive_cycle_discharge


def test_datasheet_discharge_capacity_crosscheck():
    """Cross-check simulated discharge against Samsung 50E datasheet capacity (5.0 Ah)."""
    cells = load_cells()
    cell = cells["samsung_inr21700_50e"]

    # 1S1P single cell test pack
    design = PackDesign(cell_id=cell.id, ns=1, np=1, cooling=CoolingType.PASSIVE)

    # Standard datasheet 0.2C discharge current (1.0 A) at nominal 3.63 V -> ~3.63 W
    duration_s = 18000  # 5 hours at 0.2C
    power_profile_W = np.full(duration_s, 3.63)

    usable_energy_Wh, discharge_ts = simulate_drive_cycle_discharge(
        cell=cell,
        design=design,
        power_profile_W=power_profile_W,
        dt_s=1.0,
        inverter_eff=1.0,  # Pure cell level
    )

    # Datasheet rated energy at 0.2C: 3.63 V * 5.0 Ah = 18.15 Wh
    expected_energy_Wh = cell.nominal_voltage_V * cell.capacity_Ah
    deviation_pct = abs(usable_energy_Wh - expected_energy_Wh) / expected_energy_Wh * 100.0

    print(f"Datasheet Cross-Check: Simulated {usable_energy_Wh:.2f} Wh vs Datasheet {expected_energy_Wh:.2f} Wh")
    print(f"Deviation: {deviation_pct:.2f}% (Tolerance: < 5.0%)")

    assert deviation_pct < 5.0, f"Simulated discharge deviated by {deviation_pct:.2f}% from datasheet!"

