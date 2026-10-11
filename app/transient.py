"""Single-process, bounded, expiring private workflow state (not a durable queue)."""
from collections import OrderedDict
from dataclasses import dataclass, field
from threading import RLock
from time import monotonic
from uuid import uuid4


@dataclass
class Workflow:
    owner: str
    resume: str
    profile: dict
    expires: float
    jobs: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    roles: list = field(default_factory=list)
    locations: list = field(default_factory=list)
    outcomes: dict = field(default_factory=dict)
    experience_months: int | None = None
    searched: bool = False
    lock: RLock = field(default_factory=RLock)


class WorkflowStore:
    def __init__(self, ttl=1800, capacity=20):
        self.ttl, self.capacity = ttl, capacity
        self.items = OrderedDict()
        self.lock = RLock()

    def create(self, owner, resume, profile):
        with self.lock:
            self._prune()
            while len(self.items) >= self.capacity:
                self.items.popitem(last=False)
            token = uuid4().hex
            self.items[token] = Workflow(owner, resume, profile, monotonic() + self.ttl)
            return token

    def _prune(self):
        for key in list(self.items):
            if self.items[key].expires <= monotonic():
                del self.items[key]

    def get(self, token, owner):
        with self.lock:
            self._prune()
            item = self.items.get(token)
            return item if item and item.owner == owner else None
