"""
HPP Calculation utilities.

Formulas:
- Line cost = Quantity × Price per unit
- Total batch cost = Sum of all line costs
- HPP per unit = Total batch cost / Output units
- Margin amount = HPP per unit × (Target margin % / 100)
- Selling price = HPP per unit + Margin amount
- Actual margin % = ((Selling price - HPP per unit) / Selling price) × 100
- Contribution % = (Line cost / Total batch cost) × 100
"""

from typing import List, Dict, Tuple
from decimal import Decimal, ROUND_HALF_UP


def calculate_line_cost(quantity: float, price_per_unit: float) -> float:
    """Calculate line cost for an ingredient."""
    if quantity <= 0 or price_per_unit <= 0:
        return 0.0
    return round(quantity * price_per_unit, 2)


def calculate_total_batch_cost(ingredients: List[Dict]) -> float:
    """Calculate total batch cost from all ingredients."""
    total = sum(
        calculate_line_cost(ing.get('quantity', 0), ing.get('price_per_unit', 0))
        for ing in ingredients
        if ing.get('name')  # Only count ingredients with names
    )
    return round(total, 2)


def calculate_hpp_per_unit(total_batch_cost: float, output_units: int) -> float:
    """Calculate HPP (cost) per unit."""
    if output_units <= 0:
        return 0.0
    return round(total_batch_cost / output_units, 2)


def calculate_selling_price(hpp_per_unit: float, target_margin_percent: float) -> float:
    """
    Calculate suggested selling price based on target margin.

    Formula: Selling price = HPP / (1 - margin%)
    This ensures the margin is calculated on the selling price, not on cost.

    Alternative (markup on cost): Selling price = HPP × (1 + margin%)
    Using markup formula as per PRD: Selling price = HPP + (HPP × margin%)
    """
    if hpp_per_unit <= 0:
        return 0.0

    margin_decimal = target_margin_percent / 100
    # Markup formula (as per PRD example)
    margin_amount = hpp_per_unit * margin_decimal
    return round(hpp_per_unit + margin_amount, 2)


def calculate_margin_percent(hpp_per_unit: float, selling_price: float) -> float:
    """
    Calculate actual margin percentage from selling price.

    Formula: Margin % = ((Selling price - HPP) / Selling price) × 100
    """
    if selling_price <= 0 or hpp_per_unit <= 0:
        return 0.0

    margin = ((selling_price - hpp_per_unit) / selling_price) * 100
    return round(margin, 2)


def calculate_margin_from_cost(hpp_per_unit: float, selling_price: float) -> float:
    """
    Calculate margin percentage based on cost (markup percentage).

    Formula: Markup % = ((Selling price - HPP) / HPP) × 100
    """
    if hpp_per_unit <= 0:
        return 0.0

    markup = ((selling_price - hpp_per_unit) / hpp_per_unit) * 100
    return round(markup, 2)


def calculate_contribution_percent(line_cost: float, total_batch_cost: float) -> float:
    """Calculate contribution percentage of an ingredient to total cost."""
    if total_batch_cost <= 0:
        return 0.0
    return round((line_cost / total_batch_cost) * 100, 2)


def calculate_all(
    ingredients: List[Dict],
    output_units: int,
    target_margin_percent: float,
    actual_selling_price: float = None,
    operational_cost: float = 0.0,
    other_cost: float = 0.0
) -> Dict:
    """
    Calculate all HPP metrics.

    Returns a dictionary with all calculated values.
    """
    # Calculate line costs and total for ingredients
    processed_ingredients = []
    material_cost = 0.0

    for ing in ingredients:
        name = ing.get('name', '').strip()
        if not name:
            continue

        quantity = float(ing.get('quantity', 0) or 0)
        price_per_unit = float(ing.get('price_per_unit', 0) or 0)
        unit = ing.get('unit', 'unit')

        line_cost = calculate_line_cost(quantity, price_per_unit)
        material_cost += line_cost

        processed_ingredients.append({
            'name': name,
            'quantity': quantity,
            'unit': unit,
            'price_per_unit': price_per_unit,
            'line_cost': line_cost,
            'contribution_percent': 0  # Will be calculated after we have total
        })

    # Total batch cost = material + operational + other
    total_batch_cost = material_cost + operational_cost + other_cost

    # Calculate contribution percentages (based on total batch cost)
    for ing in processed_ingredients:
        ing['contribution_percent'] = calculate_contribution_percent(
            ing['line_cost'], total_batch_cost
        )

    # Calculate operational and other cost contribution
    operational_contribution = calculate_contribution_percent(operational_cost, total_batch_cost)
    other_contribution = calculate_contribution_percent(other_cost, total_batch_cost)

    # Calculate HPP and selling price
    hpp_per_unit = calculate_hpp_per_unit(total_batch_cost, output_units)
    suggested_selling_price = calculate_selling_price(hpp_per_unit, target_margin_percent)

    # Calculate actual margin if selling price provided
    if actual_selling_price and actual_selling_price > 0:
        actual_margin = calculate_margin_from_cost(hpp_per_unit, actual_selling_price)
    else:
        actual_selling_price = suggested_selling_price
        actual_margin = target_margin_percent

    # Calculate gap vs target
    gap_vs_target = round(actual_margin - target_margin_percent, 2)

    # Determine margin status
    if actual_margin >= target_margin_percent:
        margin_status = 'success'  # Green
    elif actual_margin >= target_margin_percent - 5:
        margin_status = 'warning'  # Yellow
    else:
        margin_status = 'danger'  # Red

    return {
        'ingredients': processed_ingredients,
        'material_cost': round(material_cost, 2),
        'operational_cost': round(operational_cost, 2),
        'other_cost': round(other_cost, 2),
        'operational_contribution': operational_contribution,
        'other_contribution': other_contribution,
        'total_batch_cost': round(total_batch_cost, 2),
        'output_units': output_units,
        'target_margin_percent': target_margin_percent,
        'hpp_per_unit': hpp_per_unit,
        'suggested_selling_price': suggested_selling_price,
        'actual_selling_price': actual_selling_price,
        'actual_margin_percent': actual_margin,
        'gap_vs_target': gap_vs_target,
        'margin_status': margin_status
    }


def get_top_contributors(ingredients: List[Dict], top_n: int = 3) -> List[Dict]:
    """
    Get top N cost contributors from ingredients list.

    Returns ingredients sorted by contribution percentage (descending).
    """
    # Filter out ingredients without names or with zero cost
    valid_ingredients = [
        ing for ing in ingredients
        if ing.get('name') and ing.get('line_cost', 0) > 0
    ]

    # Sort by line cost descending
    sorted_ingredients = sorted(
        valid_ingredients,
        key=lambda x: x.get('line_cost', 0),
        reverse=True
    )

    return sorted_ingredients[:top_n]


def validate_ingredients(ingredients: List[Dict]) -> Tuple[bool, List[str]]:
    """
    Validate ingredients data.

    Returns (is_valid, error_messages).
    """
    errors = []
    has_valid_ingredient = False

    for i, ing in enumerate(ingredients):
        row_num = i + 1
        name = ing.get('name', '').strip()

        # Skip empty rows
        if not name:
            continue

        has_valid_ingredient = True

        # Validate name length
        if len(name) > 100:
            errors.append(f"Baris {row_num}: Nama bahan terlalu panjang (max 100 karakter)")

        # Validate quantity
        quantity = ing.get('quantity')
        if quantity is None or quantity <= 0:
            errors.append(f"Baris {row_num}: Kuantitas harus lebih dari 0")

        # Validate price
        price = ing.get('price_per_unit')
        if price is None or price <= 0:
            errors.append(f"Baris {row_num}: Harga per unit harus lebih dari 0")

        # Validate unit
        unit = ing.get('unit', '').strip()
        if not unit:
            errors.append(f"Baris {row_num}: Satuan harus diisi")

    if not has_valid_ingredient:
        errors.append("Minimal harus ada 1 bahan yang valid")

    return len(errors) == 0, errors
