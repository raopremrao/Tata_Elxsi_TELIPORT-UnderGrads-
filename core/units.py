"""Physical Units and Conversion Helpers for Q-Pack."""

def wh_to_kwh(wh: float) -> float:
    """Convert Watt-hours to Kilowatt-hours."""
    return wh / 1000.0

def kwh_to_wh(kwh: float) -> float:
    """Convert Kilowatt-hours to Watt-hours."""
    return kwh * 1000.0

def s_to_min(s: float) -> float:
    """Convert seconds to minutes."""
    return s / 60.0

def min_to_s(m: float) -> float:
    """Convert minutes to seconds."""
    return m * 60.0

def c_to_k(celsius: float) -> float:
    """Convert Celsius to Kelvin."""
    return celsius + 273.15

def k_to_c(kelvin: float) -> float:
    """Convert Kelvin to Celsius."""
    return kelvin - 273.15

def mm_to_m(mm: float) -> float:
    """Convert millimeters to meters."""
    return mm / 1000.0

def m3_to_l(m3: float) -> float:
    """Convert cubic meters to Liters."""
    return m3 * 1000.0

def l_to_m3(liters: float) -> float:
    """Convert Liters to cubic meters."""
    return liters / 1000.0

def g_to_kg(g: float) -> float:
    """Convert grams to kilograms."""
    return g / 1000.0

def kg_to_g(kg: float) -> float:
    """Convert kilograms to grams."""
    return kg * 1000.0

def mohm_to_ohm(mohm: float) -> float:
    """Convert milliOhms to Ohms."""
    return mohm / 1000.0

def ohm_to_mohm(ohm: float) -> float:
    """Convert Ohms to milliOhms."""
    return ohm * 1000.0

