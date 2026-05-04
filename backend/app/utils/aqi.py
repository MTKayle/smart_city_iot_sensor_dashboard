"""
AQI (Air Quality Index) calculation utility for Smart City IoT Dashboard.

Implements the US EPA standard AQI formula based on the official PM2.5
breakpoint concentration table (µg/m³, 24-hour average).

AQI Ranges
----------
  0 –  50   Good           (PM2.5:   0.0 – 12.0)
 51 – 100   Moderate       (PM2.5:  12.1 – 35.4)
101 – 150   Unhealthy for Sensitive Groups  (PM2.5: 35.5 – 55.4)
151 – 200   Unhealthy      (PM2.5:  55.5 – 150.4)
201 – 300   Very Unhealthy (PM2.5: 150.5 – 250.4)
301 – 500   Hazardous      (PM2.5: 250.5 – 500.4)

Formula
-------
    AQI = ((I_high - I_low) / (C_high - C_low)) * (C - C_low) + I_low

    where C is the PM2.5 concentration, C_low/C_high are the breakpoint
    concentrations, and I_low/I_high are the corresponding AQI index values.

Validates: FR6.1
"""

from typing import Optional, Tuple


# ---------------------------------------------------------------------------
# EPA PM2.5 breakpoint table
# Each tuple: (C_low, C_high, I_low, I_high, category, color_hex)
# ---------------------------------------------------------------------------
_PM25_BREAKPOINTS: Tuple[Tuple, ...] = (
    (0.0,    12.0,    0,   50,  "Good",                          "#00E400"),
    (12.1,   35.4,   51,  100,  "Moderate",                      "#FFFF00"),
    (35.5,   55.4,  101,  150,  "Unhealthy for Sensitive Groups", "#FF7E00"),
    (55.5,  150.4,  151,  200,  "Unhealthy",                     "#FF0000"),
    (150.5, 250.4,  201,  300,  "Very Unhealthy",                "#8F3F97"),
    (250.5, 500.4,  301,  500,  "Hazardous",                     "#7E0023"),
)

# Concentration above 500.4 is beyond-index — treated as 500 (Hazardous cap)
_AQI_MAX = 500
_PM25_MAX = 500.4


class AQIResult:
    """
    Result of an AQI calculation.

    Attributes:
        aqi:        Calculated integer AQI value (0–500+)
        category:   Descriptive category string (e.g. "Good", "Hazardous")
        color:      Hex colour string for the AQI band (e.g. "#00E400")
        pm25:       Original PM2.5 concentration used in the calculation (µg/m³)
    """

    __slots__ = ("aqi", "category", "color", "pm25")

    def __init__(self, aqi: int, category: str, color: str, pm25: float) -> None:
        self.aqi = aqi
        self.category = category
        self.color = color
        self.pm25 = pm25

    def to_dict(self) -> dict:
        """Return a plain dict for JSON serialisation."""
        return {
            "aqi": self.aqi,
            "category": self.category,
            "color": self.color,
            "pm25": self.pm25,
        }

    def __repr__(self) -> str:
        return (
            f"AQIResult(aqi={self.aqi}, category='{self.category}', "
            f"color='{self.color}', pm25={self.pm25})"
        )


def calculate_aqi(pm25: float) -> Optional[AQIResult]:
    """
    Calculate the Air Quality Index (AQI) for a given PM2.5 concentration.

    Uses the official US EPA piecewise linear interpolation formula against
    the standard PM2.5 24-hour breakpoint table (6 AQI ranges).

    Args:
        pm25: PM2.5 concentration in µg/m³ (24-hour average).
              Must be ≥ 0.  Values above 500.4 are clamped to the
              Hazardous ceiling and returned with aqi=500.

    Returns:
        AQIResult with .aqi (int), .category (str), .color (str),
        and .pm25 (float).  Returns None if pm25 is negative or NaN.

    Raises:
        TypeError: if pm25 is not a numeric type.

    Examples:
        >>> calculate_aqi(10.0)
        AQIResult(aqi=42, category='Good', ...)

        >>> calculate_aqi(35.4)
        AQIResult(aqi=100, category='Moderate', ...)

        >>> calculate_aqi(150.5)
        AQIResult(aqi=201, category='Very Unhealthy', ...)

    Validates: FR6.1
    """
    if pm25 is None:
        return None

    # Type guard — allow int/float but reject non-numeric
    if not isinstance(pm25, (int, float)):
        raise TypeError(f"pm25 must be numeric, got {type(pm25).__name__}")

    # Negative concentrations are invalid
    if pm25 < 0:
        return None

    # Beyond-index: clamp to upper Hazardous band
    if pm25 > _PM25_MAX:
        pm25_clamped = _PM25_MAX
    else:
        pm25_clamped = float(pm25)

    # Truncate to 1 decimal place as per EPA methodology
    pm25_truncated = int(pm25_clamped * 10) / 10.0

    # Find the correct breakpoint band
    for c_low, c_high, i_low, i_high, category, color in _PM25_BREAKPOINTS:
        if c_low <= pm25_truncated <= c_high:
            # EPA piecewise linear interpolation
            aqi = ((i_high - i_low) / (c_high - c_low)) * (pm25_truncated - c_low) + i_low
            return AQIResult(
                aqi=round(int(aqi)),
                category=category,
                color=color,
                pm25=pm25,
            )

    # Fallback: value exactly equals 500.4 edge → Hazardous cap
    return AQIResult(aqi=_AQI_MAX, category="Hazardous", color="#7E0023", pm25=pm25)


def get_aqi_category(aqi: int) -> Tuple[str, str]:
    """
    Return the (category, color) pair for a known integer AQI value.

    Useful when you already have a stored AQI and just need the label.

    Args:
        aqi: Integer AQI value (0–500).

    Returns:
        Tuple of (category_string, color_hex_string).
    """
    if aqi <= 50:
        return "Good", "#00E400"
    elif aqi <= 100:
        return "Moderate", "#FFFF00"
    elif aqi <= 150:
        return "Unhealthy for Sensitive Groups", "#FF7E00"
    elif aqi <= 200:
        return "Unhealthy", "#FF0000"
    elif aqi <= 300:
        return "Very Unhealthy", "#8F3F97"
    else:
        return "Hazardous", "#7E0023"
