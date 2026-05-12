# Agent Security Framework

Two P0 security modules for SkyCetus Agent protection:

## audit_logger.py
PostgreSQL append-only audit log with HMAC-SHA256 signing and hash chain.

## noose_protocol.py
Agent anomaly detection and auto-freeze protocol (3-strike rule).
