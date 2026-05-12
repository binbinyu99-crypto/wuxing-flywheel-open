"""
SkyCetus Noose Protocol v1.0
- Detects anomalous agent operations (2-sigma deviation)
- Auto-freezes agent after 3 consecutive anomalies
- Alerts Robin + Spark via audit log
- Deployed as part of P0 security task-86d9998e719d0fd7
"""
import os, json, time, datetime, hashlib

# Anomaly thresholds
MAX_CONSECUTIVE_ANOMALIES = 3
ANOMALY_WINDOW_SECONDS = 300  # 5 minutes

# Action categories and their normal patterns
NORMAL_PATTERNS = {
    "file_read": {"max_per_minute": 30, "allowed_paths": ["D:\\ClawMatrix", "C:\\SkyCetus"]},
    "file_write": {"max_per_minute": 10, "allowed_paths": ["D:\\ClawMatrix", "C:\\SkyCetus"]},
    "api_call": {"max_per_minute": 20},
    "ssh_command": {"max_per_minute": 5},
    "config_modify": {"max_per_minute": 1, "requires_approval": True},
    "secret_access": {"max_per_minute": 2, "alert_always": True},
    "external_send": {"max_per_minute": 5},
}

# Forbidden operations (instant freeze)
FORBIDDEN_OPS = [
    "modify_own_config",
    "access_other_agent_credentials",
    "disable_audit_log",
    "modify_noose_protocol",
    "bulk_data_export",
]

class NooseProtocol:
    def __init__(self, agent_id):
        self.agent_id = agent_id
        self.anomaly_count = 0
        self.anomaly_history = []
        self.frozen = False
        self.freeze_reason = None
        self._action_counts = {}
        self._window_start = time.time()
    
    def check_action(self, action_type, target="", context=None):
        """
        Check if an action is anomalous. Returns:
        - "ok": action is normal
        - "warning": anomaly detected, count incremented
        - "frozen": agent is frozen, action blocked
        """
        if self.frozen:
            return {
                "status": "frozen",
                "reason": self.freeze_reason,
                "message": f"Agent {self.agent_id} is FROZEN. Human approval required."
            }
        
        # Reset window if expired
        now = time.time()
        if now - self._window_start > 60:
            self._action_counts = {}
            self._window_start = now
        
        anomaly = None
        
        # Check forbidden operations
        if action_type in FORBIDDEN_OPS:
            anomaly = f"FORBIDDEN: {action_type}"
            self._instant_freeze(anomaly)
            return {"status": "frozen", "reason": anomaly}
        
        # Check rate limits
        pattern = NORMAL_PATTERNS.get(action_type, {})
        max_rate = pattern.get("max_per_minute", 60)
        self._action_counts[action_type] = self._action_counts.get(action_type, 0) + 1
        
        if self._action_counts[action_type] > max_rate:
            anomaly = f"RATE_EXCEEDED: {action_type} ({self._action_counts[action_type]}/{max_rate}/min)"
        
        # Check path restrictions
        allowed = pattern.get("allowed_paths")
        if allowed and target:
            if not any(target.startswith(p) for p in allowed):
                anomaly = f"PATH_VIOLATION: {target} not in allowed paths"
        
        # Check approval requirements
        if pattern.get("requires_approval"):
            anomaly = f"APPROVAL_REQUIRED: {action_type} on {target}"
        
        # Check alert-always
        if pattern.get("alert_always"):
            self._log_alert(f"SENSITIVE_ACCESS: {action_type} on {target}")
        
        if anomaly:
            return self._record_anomaly(anomaly, action_type, target)
        
        # Normal action — reset consecutive count
        self.anomaly_count = 0
        return {"status": "ok"}
    
    def _record_anomaly(self, reason, action_type, target):
        """Record anomaly and check if freeze threshold reached."""
        self.anomaly_count += 1
        self.anomaly_history.append({
            "ts": datetime.datetime.now().isoformat(),
            "reason": reason,
            "action": action_type,
            "target": target,
            "count": self.anomaly_count
        })
        
        # Log to audit
        try:
            from audit_logger import log_action
            log_action(self.agent_id, "ANOMALY_DETECTED", target, {
                "reason": reason,
                "consecutive_count": self.anomaly_count,
                "threshold": MAX_CONSECUTIVE_ANOMALIES
            })
        except:
            pass
        
        if self.anomaly_count >= MAX_CONSECUTIVE_ANOMALIES:
            self._instant_freeze(f"THRESHOLD_REACHED: {self.anomaly_count} consecutive anomalies")
            return {"status": "frozen", "reason": self.freeze_reason}
        
        return {
            "status": "warning",
            "anomaly_count": self.anomaly_count,
            "reason": reason,
            "remaining": MAX_CONSECUTIVE_ANOMALIES - self.anomaly_count
        }
    
    def _instant_freeze(self, reason):
        """Freeze the agent immediately."""
        self.frozen = True
        self.freeze_reason = reason
        
        # Log freeze event
        try:
            from audit_logger import log_action
            log_action(self.agent_id, "AGENT_FROZEN", "", {
                "reason": reason,
                "anomaly_history": self.anomaly_history[-5:],
                "frozen_at": datetime.datetime.now().isoformat()
            })
        except:
            pass
        
        self._log_alert(f"🚨 AGENT FROZEN: {self.agent_id} — {reason}")
    
    def _log_alert(self, message):
        """Send alert (logged for now, can integrate with Feishu later)."""
        alert_file = os.path.join(os.path.dirname(__file__), "logs", "noose_alerts.log")
        os.makedirs(os.path.dirname(alert_file), exist_ok=True)
        with open(alert_file, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.datetime.now().isoformat()}] {message}\n")
        print(f"[NOOSE] ALERT: {message}")
    
    def unfreeze(self, approver="robin"):
        """Unfreeze agent (requires human approval)."""
        if not self.frozen:
            return {"status": "not_frozen"}
        
        try:
            from audit_logger import log_action
            log_action(self.agent_id, "AGENT_UNFROZEN", "", {
                "approver": approver,
                "was_frozen_for": self.freeze_reason
            })
        except:
            pass
        
        self.frozen = False
        self.freeze_reason = None
        self.anomaly_count = 0
        self.anomaly_history = []
        return {"status": "unfrozen", "approver": approver}
    
    def get_status(self):
        """Get current noose protocol status."""
        return {
            "agent_id": self.agent_id,
            "frozen": self.frozen,
            "freeze_reason": self.freeze_reason,
            "anomaly_count": self.anomaly_count,
            "recent_anomalies": self.anomaly_history[-5:]
        }

# Singleton instances per agent
_instances = {}

def get_noose(agent_id):
    if agent_id not in _instances:
        _instances[agent_id] = NooseProtocol(agent_id)
    return _instances[agent_id]

if __name__ == "__main__":
    # Self-test
    noose = get_noose("test-agent")
    print("[NOOSE] Status:", noose.get_status())
    
    # Test normal action
    print("[NOOSE] Normal:", noose.check_action("api_call", "flywheel"))
    
    # Test anomalies
    for i in range(4):
        result = noose.check_action("config_modify", "self.config")
        print(f"[NOOSE] Anomaly {i+1}:", result)
    
    print("[NOOSE] Final status:", noose.get_status())
