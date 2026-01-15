"""
Distributor/Reseller HPP Calculator Module
Calculates Cost of Goods Sold for resellers and distributors
"""


def validate_distributor_inputs(products: list) -> tuple[bool, list]:
    """
    Validate distributor product inputs.

    Args:
        products: List of product dicts with keys:
            - name: Product name
            - buy_price: Price per unit from supplier
            - quantity: Number of units purchased
            - shipping_cost: Total shipping cost for this product
            - handling_cost: Warehouse/handling cost

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []

    if not products:
        errors.append("Minimal 1 produk harus diisi.")
        return False, errors

    for i, product in enumerate(products):
        row_num = i + 1

        if not product.get('name') or not str(product['name']).strip():
            errors.append(f"Baris {row_num}: Nama produk harus diisi.")
            continue

        if product.get('buy_price', 0) <= 0:
            errors.append(f"Baris {row_num}: Harga beli harus lebih dari 0.")

        if product.get('quantity', 0) <= 0:
            errors.append(f"Baris {row_num}: Quantity harus lebih dari 0.")

    return len(errors) == 0, errors


def calculate_distributor_hpp(
    buy_price: float,
    quantity: int,
    shipping_cost: float = 0,
    handling_cost: float = 0,
    target_margin_percent: float = 30
) -> dict:
    """
    Calculate HPP for a distributor/reseller product.

    Args:
        buy_price: Price per unit from supplier
        quantity: Number of units purchased
        shipping_cost: Total shipping cost
        handling_cost: Warehouse/handling cost
        target_margin_percent: Target profit margin percentage

    Returns:
        Dictionary with calculation results
    """
    # Calculate cost components per unit
    shipping_per_unit = shipping_cost / quantity if quantity > 0 else 0
    handling_per_unit = handling_cost / quantity if quantity > 0 else 0

    # HPP per unit
    hpp_per_unit = buy_price + shipping_per_unit + handling_per_unit

    # Total investment
    total_investment = (buy_price * quantity) + shipping_cost + handling_cost

    # Suggested selling price based on margin
    # Formula: Selling Price = HPP / (1 - margin%)
    margin_decimal = target_margin_percent / 100
    if margin_decimal >= 1:
        margin_decimal = 0.99  # Cap at 99% margin

    suggested_selling_price = hpp_per_unit / (1 - margin_decimal) if margin_decimal < 1 else hpp_per_unit * 2

    # Profit per unit
    profit_per_unit = suggested_selling_price - hpp_per_unit

    # Breakeven calculation (units needed to cover investment at suggested price)
    breakeven_units = 0
    if profit_per_unit > 0:
        breakeven_units = int(total_investment / profit_per_unit) + 1

    return {
        'buy_price': buy_price,
        'quantity': quantity,
        'shipping_cost': shipping_cost,
        'handling_cost': handling_cost,
        'shipping_per_unit': round(shipping_per_unit, 2),
        'handling_per_unit': round(handling_per_unit, 2),
        'hpp_per_unit': round(hpp_per_unit, 2),
        'total_investment': round(total_investment, 2),
        'target_margin_percent': target_margin_percent,
        'suggested_selling_price': round(suggested_selling_price, 2),
        'profit_per_unit': round(profit_per_unit, 2),
        'breakeven_units': breakeven_units,
        'cost_breakdown': {
            'buy_price_percent': round((buy_price / hpp_per_unit) * 100, 1) if hpp_per_unit > 0 else 0,
            'shipping_percent': round((shipping_per_unit / hpp_per_unit) * 100, 1) if hpp_per_unit > 0 else 0,
            'handling_percent': round((handling_per_unit / hpp_per_unit) * 100, 1) if hpp_per_unit > 0 else 0,
        }
    }


def calculate_distributor_batch(products: list, target_margin_percent: float = 30) -> dict:
    """
    Calculate HPP for multiple products in a batch.

    Args:
        products: List of product dicts
        target_margin_percent: Default target margin

    Returns:
        Dictionary with batch calculation results
    """
    results = []
    total_investment = 0
    total_potential_revenue = 0

    for product in products:
        if not product.get('name') or not str(product['name']).strip():
            continue

        result = calculate_distributor_hpp(
            buy_price=float(product.get('buy_price', 0)),
            quantity=int(product.get('quantity', 1)),
            shipping_cost=float(product.get('shipping_cost', 0)),
            handling_cost=float(product.get('handling_cost', 0)),
            target_margin_percent=target_margin_percent
        )
        result['name'] = str(product['name']).strip()
        results.append(result)

        total_investment += result['total_investment']
        total_potential_revenue += result['suggested_selling_price'] * result['quantity']

    total_potential_profit = total_potential_revenue - total_investment

    return {
        'products': results,
        'total_investment': round(total_investment, 2),
        'total_potential_revenue': round(total_potential_revenue, 2),
        'total_potential_profit': round(total_potential_profit, 2),
        'overall_margin_percent': round((total_potential_profit / total_potential_revenue) * 100, 1) if total_potential_revenue > 0 else 0
    }
