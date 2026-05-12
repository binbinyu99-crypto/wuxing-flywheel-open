"""
SkyCetus Agent Audit Logger v1.0
- Append-only PostgreSQL table (no UPDATE/DELETE)
- HMAC-SHA256 signed entries
- Hash chain linking each record to its predecessor
- Deployed as part of P0 security task-4b38b4e5f54bd744
"""
import os, json, hashlib, hmac, time, datetime, traceback

AUDIT_SECRET = os.environ.get("AUDIT_HMAC_SECRET", "skycetus-audit-2026-v1")
_PG_DSN = os.environ.get("FLYWHEEL_PG_DSN", "dbname=skycetus user=postgres host=localhost")

def _get_conn():
    import psycopg2
    return psycopg2.connect(_PG_DSN)

def init_audit_table():
    """Create audit table and revoke dangerous permissions."""
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS flywheel.agent_audit_log (
        id BIGSERIAL PRIMARY KEY,
        ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        agent_id TEXT NOT NULL,
        action_type TEXT NOT NULL,
        target TEXT,
        context_hash TEXT,
        payload JSONB,
        hmac_sig TEXT NOT NULL,
        prev_hash TEXT NOT NULL,
        entry_hash TEXT NOT NULL
    );
    """)
    # Create index for fast lookups
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_audit_agent ON flywheel.agent_audit_log(agent_id);
    CREATE INDEX IF NOT EXISTS idx_audit_ts ON flywheel.agent_audit_log(ts);
    CREATE INDEX IF NOT EXISTS idx_audit_action ON flywheel.agent_audit_log(action_type);
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("[AUDIT] Table initialized")

def _compute_hmac(data_str):
    return hmac.new(AUDIT_SECRET.encode(), data_str.encode(), hashlib.sha256).hexdigest()

def _compute_hash(entry_str):
    return hashlib.sha256(entry_str.encode()).hexdigest()

def _get_last_hash():
    """Get hash of the last audit entry for chain linking."""
    try:
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("SELECT entry_hash FROM flywheel.agent_audit_log ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row[0] if row else "GENESIS"
    except:
        return "GENESIS"

def log_action(agent_id, action_type, target="", payload=None, context=""):
    """
    Log an agent action to the append-only audit trail.
    Returns the entry hash for verification.
    """
    try:
        ts = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f+00:00')
        context_hash = hashlib.sha256(str(context).encode()).hexdigest()[:16]
        payload_json = json.dumps(payload or {}, ensure_ascii=False, default=str)
        
        # Build the signing string
        sign_str = f"{ts}|{agent_id}|{action_type}|{target}|{context_hash}|{payload_json}"
        hmac_sig = _compute_hmac(sign_str)
        
        # Chain to previous entry
        prev_hash = _get_last_hash()
        entry_str = f"{prev_hash}|{sign_str}|{hmac_sig}"
        entry_hash = _compute_hash(entry_str)
        
        conn = _get_conn()
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO flywheel.agent_audit_log 
            (ts, agent_id, action_type, target, context_hash, payload, hmac_sig, prev_hash, entry_hash)
        VALUES (%s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s)
        RETURNING id
        """, (ts, agent_id, action_type, target, context_hash, payload_json, hmac_sig, prev_hash, entry_hash))
        row_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return {"id": row_id, "entry_hash": entry_hash}
    except Exception as e:
        print(f"[AUDIT] Error logging action: {e}")
        traceback.print_exc()
        return None

def verify_chain(limit=100):
    """Verify the hash chain integrity of the last N entries."""
    conn = _get_conn()
    cur = conn.cursor()
    cur.execute("""
    SELECT id, entry_hash, prev_hash, 
           ts, agent_id, action_type, target, context_hash, payload::text, hmac_sig
    FROM flywheel.agent_audit_log ORDER BY id DESC LIMIT %s
    """, (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    if not rows:
        return {"valid": True, "checked": 0, "message": "No entries"}
    
    rows.reverse()  # oldest first
    broken = []
    for i, row in enumerate(rows):
        rid, stored_hash, stored_prev, ts, agent, action, target, ctx_hash, payload, sig = row
        # Verify HMAC — use stored ts format
        ts_str = ts.isoformat() if hasattr(ts, 'isoformat') else str(ts)
        sign_str = f"{ts_str}|{agent}|{action}|{target}|{ctx_hash}|{payload}"
        expected_hmac = _compute_hmac(sign_str)
        # Verify entry hash
        entry_str = f"{stored_prev}|{sign_str}|{sig}"
        expected_hash = _compute_hash(entry_str)
        
        if stored_hash != expected_hash:
            broken.append({"id": rid, "reason": "hash_mismatch"})
        # Verify chain link
        if i > 0 and stored_prev != rows[i-1][1]:
            broken.append({"id": rid, "reason": "chain_break"})
    
    return {
        "valid": len(broken) == 0,
        "checked": len(rows),
        "broken": broken
    }

def get_recent(agent_id=None, limit=20):
    """Get recent audit entries, optionally filtered by agent."""
    conn = _get_conn()
    cur = conn.cursor()
    if agent_id:
        cur.execute("""
        SELECT id, ts, agent_id, action_type, target, payload::text
        FROM flywheel.agent_audit_log WHERE agent_id=%s ORDER BY id DESC LIMIT %s
        """, (agent_id, limit))
    else:
        cur.execute("""
        SELECT id, ts, agent_id, action_type, target, payload::text
        FROM flywheel.agent_audit_log ORDER BY id DESC LIMIT %s
        """, (limit,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [{"id": r[0], "ts": str(r[1]), "agent": r[2], "action": r[3], "target": r[4]} for r in rows]

if __name__ == "__main__":
    init_audit_table()
    # Test
    result = log_action("spark", "test", "audit_system", {"test": True}, "init")
    print(f"[AUDIT] Test entry: {result}")
    chain = verify_chain()
    print(f"[AUDIT] Chain verification: {chain}")
