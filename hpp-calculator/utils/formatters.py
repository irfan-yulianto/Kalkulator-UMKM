"""
Formatting utilities for currency, percentages, and numbers.
Indonesian locale formatting.
"""

import re
from typing import Union


def format_currency(
    value: Union[int, float],
    symbol: str = "Rp",
    decimal_places: int = 0,
    use_separator: bool = True
) -> str:
    """
    Format a number as Indonesian currency.

    Args:
        value: The number to format
        symbol: Currency symbol (default: "Rp")
        decimal_places: Number of decimal places (default: 0)
        use_separator: Whether to use thousand separator (default: True)

    Returns:
        Formatted currency string, e.g., "Rp 1.234.567"
    """
    if value is None:
        return f"{symbol} 0"

    try:
        value = float(value)
    except (ValueError, TypeError):
        return f"{symbol} 0"

    # Round to specified decimal places
    if decimal_places == 0:
        value = int(round(value))
        formatted = f"{value:,}".replace(",", ".")
    else:
        formatted = f"{value:,.{decimal_places}f}".replace(",", "X").replace(".", ",").replace("X", ".")

    return f"{symbol} {formatted}"


def format_percentage(
    value: Union[int, float],
    decimal_places: int = 1,
    include_sign: bool = False
) -> str:
    """
    Format a number as percentage.

    Args:
        value: The percentage value (e.g., 40 for 40%)
        decimal_places: Number of decimal places
        include_sign: Whether to include + sign for positive values

    Returns:
        Formatted percentage string, e.g., "40.0%"
    """
    if value is None:
        return "0%"

    try:
        value = float(value)
    except (ValueError, TypeError):
        return "0%"

    if include_sign and value > 0:
        return f"+{value:.{decimal_places}f}%"

    return f"{value:.{decimal_places}f}%"


def format_number(
    value: Union[int, float],
    decimal_places: int = 2,
    use_separator: bool = True
) -> str:
    """
    Format a number with Indonesian thousand separator.

    Args:
        value: The number to format
        decimal_places: Number of decimal places
        use_separator: Whether to use thousand separator

    Returns:
        Formatted number string
    """
    if value is None:
        return "0"

    try:
        value = float(value)
    except (ValueError, TypeError):
        return "0"

    if decimal_places == 0:
        value = int(round(value))
        if use_separator:
            return f"{value:,}".replace(",", ".")
        return str(value)

    if use_separator:
        return f"{value:,.{decimal_places}f}".replace(",", "X").replace(".", ",").replace("X", ".")

    return f"{value:.{decimal_places}f}"


def parse_currency(value: str) -> float:
    """
    Parse a currency string to float.

    Handles formats like:
    - "Rp 1.234.567"
    - "1.234.567"
    - "1234567"
    - "Rp1234567"

    Returns:
        Float value
    """
    if value is None:
        return 0.0

    if isinstance(value, (int, float)):
        return float(value)

    # Remove currency symbol and whitespace
    cleaned = str(value).strip()
    cleaned = re.sub(r'[Rp\s]', '', cleaned, flags=re.IGNORECASE)

    # Handle Indonesian format (dots as thousand separator)
    # Check if it looks like Indonesian format (has dots but no comma or single comma for decimals)
    if '.' in cleaned and ',' not in cleaned:
        # Could be Indonesian thousand separator or decimal point
        # If multiple dots, it's thousand separator
        if cleaned.count('.') > 1:
            cleaned = cleaned.replace('.', '')
        # If single dot with 3+ digits after, it's thousand separator
        elif '.' in cleaned:
            parts = cleaned.split('.')
            if len(parts) == 2 and len(parts[1]) >= 3:
                cleaned = cleaned.replace('.', '')
    elif ',' in cleaned:
        # Has comma - could be Indonesian decimal separator
        # Replace dots (thousand sep) and comma (decimal)
        cleaned = cleaned.replace('.', '').replace(',', '.')

    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def parse_number(value: str) -> float:
    """
    Parse a number string to float, handling Indonesian format.

    Returns:
        Float value
    """
    return parse_currency(value)


def format_gap(value: float, decimal_places: int = 1) -> str:
    """
    Format gap/difference value with sign and 'pp' (percentage points) suffix.

    Args:
        value: The gap value
        decimal_places: Number of decimal places

    Returns:
        Formatted string like "+2.5 pp" or "-3.0 pp"
    """
    if value is None:
        return "0 pp"

    try:
        value = float(value)
    except (ValueError, TypeError):
        return "0 pp"

    if value > 0:
        return f"+{value:.{decimal_places}f} pp"
    elif value < 0:
        return f"{value:.{decimal_places}f} pp"
    else:
        return "0 pp"


def format_unit_options() -> list:
    """
    Get list of common unit options.

    Returns:
        List of unit strings
    """
    return [
        "kg",
        "gram",
        "liter",
        "ml",
        "meter",
        "cm",
        "piece",
        "pcs",
        "pack",
        "box",
        "lusin",
        "unit",
        "porsi",
        "buah",
        "lembar",
        "botol",
        "kaleng",
        "sachet",
        "bungkus"
    ]


def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.

    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated text
    """
    if not text:
        return ""

    if len(text) <= max_length:
        return text

    return text[:max_length - len(suffix)] + suffix
