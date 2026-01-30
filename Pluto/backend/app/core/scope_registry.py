"""
Central scope registry
Tracks last active scope per user/session
"""

from typing import Dict, Optional

# Simple in-memory store (safe for single-node dev)
_last_scope_by_user: Dict[str, str] = {}


def set_last_scope(user_id: str, scope_id: str) -> None:
    _last_scope_by_user[user_id] = scope_id


def get_last_scope(user_id: str) -> Optional[str]:
    return _last_scope_by_user.get(user_id)