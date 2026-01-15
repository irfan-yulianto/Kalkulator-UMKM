"""
Service/Jasa HPP Calculator Module
Calculates Cost of Goods Sold for service-based businesses
"""


def validate_service_inputs(services: list) -> tuple[bool, list]:
    """
    Validate service inputs.

    Args:
        services: List of service dicts with keys:
            - name: Service name
            - duration_minutes: Duration in minutes
            - labor_rate_per_hour: Labor cost per hour
            - material_cost: Material/consumable cost
            - equipment_cost: Equipment depreciation per service

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []

    if not services:
        errors.append("Minimal 1 layanan harus diisi.")
        return False, errors

    for i, service in enumerate(services):
        row_num = i + 1

        if not service.get('name') or not str(service['name']).strip():
            errors.append(f"Baris {row_num}: Nama layanan harus diisi.")
            continue

        if service.get('duration_minutes', 0) <= 0:
            errors.append(f"Baris {row_num}: Durasi layanan harus lebih dari 0 menit.")

        if service.get('labor_rate_per_hour', 0) < 0:
            errors.append(f"Baris {row_num}: Tarif karyawan tidak boleh negatif.")

    return len(errors) == 0, errors


def calculate_service_hpp(
    duration_minutes: float,
    labor_rate_per_hour: float,
    material_cost: float = 0,
    equipment_cost: float = 0,
    target_margin_percent: float = 30
) -> dict:
    """
    Calculate HPP for a service.

    Args:
        duration_minutes: Service duration in minutes
        labor_rate_per_hour: Labor cost per hour
        material_cost: Cost of materials/consumables
        equipment_cost: Equipment depreciation per service
        target_margin_percent: Target profit margin percentage

    Returns:
        Dictionary with calculation results
    """
    # Calculate labor cost
    duration_hours = duration_minutes / 60
    labor_cost = duration_hours * labor_rate_per_hour

    # HPP per service
    hpp_per_service = labor_cost + material_cost + equipment_cost

    # Suggested selling price based on margin
    margin_decimal = target_margin_percent / 100
    if margin_decimal >= 1:
        margin_decimal = 0.99

    suggested_selling_price = hpp_per_service / (1 - margin_decimal) if margin_decimal < 1 else hpp_per_service * 2

    # Profit per service
    profit_per_service = suggested_selling_price - hpp_per_service

    # Calculate hourly earning potential
    services_per_hour = 60 / duration_minutes if duration_minutes > 0 else 0
    potential_hourly_revenue = services_per_hour * suggested_selling_price
    potential_hourly_profit = services_per_hour * profit_per_service

    return {
        'duration_minutes': duration_minutes,
        'duration_hours': round(duration_hours, 2),
        'labor_rate_per_hour': labor_rate_per_hour,
        'labor_cost': round(labor_cost, 2),
        'material_cost': material_cost,
        'equipment_cost': equipment_cost,
        'hpp_per_service': round(hpp_per_service, 2),
        'target_margin_percent': target_margin_percent,
        'suggested_selling_price': round(suggested_selling_price, 2),
        'profit_per_service': round(profit_per_service, 2),
        'services_per_hour': round(services_per_hour, 2),
        'potential_hourly_revenue': round(potential_hourly_revenue, 2),
        'potential_hourly_profit': round(potential_hourly_profit, 2),
        'cost_breakdown': {
            'labor_percent': round((labor_cost / hpp_per_service) * 100, 1) if hpp_per_service > 0 else 0,
            'material_percent': round((material_cost / hpp_per_service) * 100, 1) if hpp_per_service > 0 else 0,
            'equipment_percent': round((equipment_cost / hpp_per_service) * 100, 1) if hpp_per_service > 0 else 0,
        }
    }


def calculate_service_batch(services: list, target_margin_percent: float = 30) -> dict:
    """
    Calculate HPP for multiple services.

    Args:
        services: List of service dicts
        target_margin_percent: Default target margin

    Returns:
        Dictionary with batch calculation results
    """
    results = []
    total_hpp = 0
    total_suggested_revenue = 0

    for service in services:
        if not service.get('name') or not str(service['name']).strip():
            continue

        result = calculate_service_hpp(
            duration_minutes=float(service.get('duration_minutes', 60)),
            labor_rate_per_hour=float(service.get('labor_rate_per_hour', 0)),
            material_cost=float(service.get('material_cost', 0)),
            equipment_cost=float(service.get('equipment_cost', 0)),
            target_margin_percent=target_margin_percent
        )
        result['name'] = str(service['name']).strip()
        results.append(result)

        total_hpp += result['hpp_per_service']
        total_suggested_revenue += result['suggested_selling_price']

    avg_hpp = total_hpp / len(results) if results else 0
    avg_revenue = total_suggested_revenue / len(results) if results else 0

    return {
        'services': results,
        'total_services': len(results),
        'average_hpp': round(avg_hpp, 2),
        'average_suggested_price': round(avg_revenue, 2),
        'average_profit': round(avg_revenue - avg_hpp, 2)
    }
