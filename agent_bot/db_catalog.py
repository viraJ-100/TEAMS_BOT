# db_catalog.py
from typing import List, Dict
from db import get_connection  # reuse your existing connection factory

def fetch_app_catalog(limit: int = 10) -> List[Dict]:
    """
    Returns: [{ id, app_name, install_url, versions:[...] }, ...]
    """
    db = get_connection()
    cur = db.cursor(dictionary=True)

    cur.execute("""
        SELECT a.id, a.app_name, a.install_url
        FROM apps a
        ORDER BY a.app_name ASC
        LIMIT %s
    """, (limit,))
    apps = cur.fetchall()

    # Fetch versions for those apps
    if not apps:
        cur.close(); db.close()
        return []

    app_ids = tuple([a["id"] for a in apps])
    placeholders = ",".join(["%s"] * len(app_ids))
    cur.execute(f"""
        SELECT v.app_id, v.version, v.is_default
        FROM app_versions v
        WHERE v.app_id IN ({placeholders})
        ORDER BY v.is_default DESC, v.version ASC
    """, app_ids)
    rows = cur.fetchall()
    cur.close(); db.close()

    versions_by_app = {}
    for r in rows:
        versions_by_app.setdefault(r["app_id"], []).append(r["version"])

    for a in apps:
        a["versions"] = versions_by_app.get(a["id"], []) or ["latest"]

    return apps
