"""
Migration script to add new tip entry requirements and update position requirements.

Changes:
1. Add new tip entry requirements: Adjustments, Tips on Paycheck, Tip Out
2. Update existing positions with new requirements:
   - Waitstaff: Bank Card Sales, Bank Card Tips, Total Sales, Cash Tips, Take-Home Tips, Adjustments, Tips on Paycheck, Tip Out
   - Busser: Take-Home Tips, Adjustments, Tips on Paycheck
   - Host: Take-Home Tips, Adjustments, Tips on Paycheck
   - Cook: Take-Home Tips, Adjustments, Tips on Paycheck, Tip Out
3. Add new position: Prep with Take-Home Tips, Adjustments, Tips on Paycheck

This migration ensures all positions have the correct tip entry requirements including
the newly added fields for adjustments, tips on paycheck, and tip out.
"""
import sqlite3
import os

def create_slug(text):
    return text.lower().replace(" ", "-").replace("'", "")

def migrate():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    db_path = os.path.join(project_root, "data", "database.db")

    print(f"Looking for database at: {db_path}")

    if not os.path.exists(db_path):
        print("Database does not exist. No migration needed.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        print("Starting migration to update tip requirements and positions...")

        new_requirements = [
            {"name": "Adjustments", "field_name": "adjustments"},
            {"name": "Tips on Paycheck", "field_name": "tips_on_paycheck"},
            {"name": "Tip Out", "field_name": "tip_out"}
        ]

        requirement_ids = {}

        cursor.execute("SELECT id, name FROM tip_entry_requirements")
        existing_reqs = {row[1]: row[0] for row in cursor.fetchall()}

        for req in new_requirements:
            if req["name"] not in existing_reqs:
                print(f"Creating tip requirement: {req['name']}")
                cursor.execute("""
                    INSERT INTO tip_entry_requirements (name, slug, field_name)
                    VALUES (?, ?, ?)
                """, (req["name"], create_slug(req["name"]), req["field_name"]))
                requirement_ids[req["name"]] = cursor.lastrowid
            else:
                print(f"Tip requirement already exists: {req['name']}")
                requirement_ids[req["name"]] = existing_reqs[req["name"]]

        cursor.execute("SELECT id, name FROM tip_entry_requirements")
        all_reqs = {row[1]: row[0] for row in cursor.fetchall()}

        updated_positions = [
            {
                "name": "Waitstaff",
                "requirements": ["Bank Card Sales", "Bank Card Tips", "Total Sales", "Cash Tips", "Take-Home Tips", "Adjustments", "Tips on Paycheck", "Tip Out"]
            },
            {
                "name": "Busser",
                "requirements": ["Take-Home Tips", "Adjustments", "Tips on Paycheck"]
            },
            {
                "name": "Host",
                "requirements": ["Take-Home Tips", "Adjustments", "Tips on Paycheck"]
            },
            {
                "name": "Cook",
                "requirements": ["Take-Home Tips", "Adjustments", "Tips on Paycheck", "Tip Out"]
            },
            {
                "name": "Prep",
                "requirements": ["Take-Home Tips", "Adjustments", "Tips on Paycheck"]
            }
        ]

        cursor.execute("SELECT id, name FROM positions")
        existing_positions = {row[1]: row[0] for row in cursor.fetchall()}

        for pos in updated_positions:
            if pos["name"] not in existing_positions:
                print(f"Creating position: {pos['name']}")
                cursor.execute("""
                    INSERT INTO positions (name, slug)
                    VALUES (?, ?)
                """, (pos["name"], create_slug(pos["name"])))
                position_id = cursor.lastrowid
            else:
                print(f"Updating position: {pos['name']}")
                position_id = existing_positions[pos["name"]]
                cursor.execute("""
                    DELETE FROM position_tip_requirements
                    WHERE position_id = ?
                """, (position_id,))

            for req_name in pos["requirements"]:
                if req_name in all_reqs:
                    cursor.execute("""
                        INSERT OR IGNORE INTO position_tip_requirements (position_id, tip_requirement_id)
                        VALUES (?, ?)
                    """, (position_id, all_reqs[req_name]))
                    print(f"  - Added requirement '{req_name}' to {pos['name']}")

        conn.commit()
        print("Migration completed successfully!")

    except Exception as e:
        print(f"Error during migration: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
