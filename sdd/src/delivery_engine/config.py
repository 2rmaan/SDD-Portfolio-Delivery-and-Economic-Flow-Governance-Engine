DEFAULT_FLOW_EFFICIENCY_THRESHOLD = 0.45
HIGH_VARIANCE_MULTIPLIER = 2.0

# Maps state label patterns (case-insensitive substring match) to state types.
# First match wins. Order matters: more specific patterns should come first.
STATE_TYPE_MAP: list[tuple[str, str]] = [
    # completed
    ("done", "completed"),
    ("completed", "completed"),
    ("closed", "completed"),
    ("delivered", "completed"),
    # active
    ("in progress", "active"),
    ("active", "active"),
    ("development", "active"),
    ("review", "active"),
    # wait (explicit blocking)
    ("waiting", "wait"),
    ("blocked", "wait"),
    ("in queue", "wait"),
    ("pending approval", "wait"),
    # wait (pre-start)
    ("backlog", "wait"),
    ("to do", "wait"),
    ("created", "wait"),
    ("started", "wait"),
]
