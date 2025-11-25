import json
from datetime import datetime
from typing import List, Dict, Optional
from .db import get_connection


def save_calculation(
    name: str,
    ingredients: List[Dict],
    output_units: int,
    target_margin_percent: float,
    total_batch_cost: float,
    hpp_per_unit: float,
    suggested_selling_price: float,
    actual_selling_price: float = None,
    actual_margin_percent: float = None
) -> int:
    """Save a calculation with its ingredients to database."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Insert calculation
        cursor.execute('''
            INSERT INTO calculations (
                name, total_batch_cost, output_units, target_margin_percent,
                hpp_per_unit, suggested_selling_price, actual_selling_price,
                actual_margin_percent
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            name, total_batch_cost, output_units, target_margin_percent,
            hpp_per_unit, suggested_selling_price, actual_selling_price,
            actual_margin_percent
        ))

        calculation_id = cursor.lastrowid

        # Insert ingredients
        for ing in ingredients:
            cursor.execute('''
                INSERT INTO ingredients (
                    calculation_id, name, quantity, unit, price_per_unit,
                    line_cost, contribution_percent
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                calculation_id,
                ing['name'],
                ing['quantity'],
                ing['unit'],
                ing['price_per_unit'],
                ing['line_cost'],
                ing['contribution_percent']
            ))

        conn.commit()
        return calculation_id


def get_calculations(limit: int = 50) -> List[Dict]:
    """Get recent calculations."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM calculations ORDER BY created_at DESC LIMIT ?
        ''', (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_calculation_by_id(calculation_id: int) -> Optional[Dict]:
    """Get a calculation with its ingredients by ID."""
    with get_connection() as conn:
        cursor = conn.cursor()

        # Get calculation
        cursor.execute('SELECT * FROM calculations WHERE id = ?', (calculation_id,))
        calc_row = cursor.fetchone()

        if not calc_row:
            return None

        calculation = dict(calc_row)

        # Get ingredients
        cursor.execute('''
            SELECT * FROM ingredients WHERE calculation_id = ?
        ''', (calculation_id,))
        ing_rows = cursor.fetchall()
        calculation['ingredients'] = [dict(row) for row in ing_rows]

        return calculation


def delete_calculation(calculation_id: int) -> bool:
    """Delete a calculation and its ingredients."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM ingredients WHERE calculation_id = ?', (calculation_id,))
        cursor.execute('DELETE FROM calculations WHERE id = ?', (calculation_id,))
        conn.commit()
        return cursor.rowcount > 0


def update_calculation(calculation_id: int, **kwargs) -> bool:
    """Update a calculation."""
    allowed_fields = [
        'name', 'total_batch_cost', 'output_units', 'target_margin_percent',
        'hpp_per_unit', 'suggested_selling_price', 'actual_selling_price',
        'actual_margin_percent'
    ]

    updates = {k: v for k, v in kwargs.items() if k in allowed_fields}

    if not updates:
        return False

    with get_connection() as conn:
        cursor = conn.cursor()

        set_clause = ', '.join([f'{k} = ?' for k in updates.keys()])
        values = list(updates.values()) + [calculation_id]

        cursor.execute(f'''
            UPDATE calculations
            SET {set_clause}, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', values)

        conn.commit()
        return cursor.rowcount > 0


def save_template(name: str, ingredients: List[Dict], output_units: int = 1, target_margin_percent: float = 40) -> int:
    """Save an ingredient template."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO templates (name, ingredients_json, output_units, target_margin_percent)
            VALUES (?, ?, ?, ?)
        ''', (name, json.dumps(ingredients), output_units, target_margin_percent))
        conn.commit()
        return cursor.lastrowid


def get_templates() -> List[Dict]:
    """Get all templates."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM templates ORDER BY created_at DESC')
        rows = cursor.fetchall()
        templates = []
        for row in rows:
            template = dict(row)
            template['ingredients'] = json.loads(template['ingredients_json'])
            del template['ingredients_json']
            templates.append(template)
        return templates


def get_template_by_id(template_id: int) -> Optional[Dict]:
    """Get a template by ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM templates WHERE id = ?', (template_id,))
        row = cursor.fetchone()
        if not row:
            return None
        template = dict(row)
        template['ingredients'] = json.loads(template['ingredients_json'])
        del template['ingredients_json']
        return template


def delete_template(template_id: int) -> bool:
    """Delete a template."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM templates WHERE id = ?', (template_id,))
        conn.commit()
        return cursor.rowcount > 0
