"""
World data model — a reusable synthetic audience.

A World wraps an existing project + Zep graph + generated personas so it can
be re-targeted with new "what-if" prompts (variant runs) without rebuilding
the expensive graph/persona stages.
"""

import os
import json
import uuid
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..config import Config


@dataclass
class World:
    world_id: str
    name: str
    description: str
    audience_summary: str
    project_id: str
    graph_id: str
    source_simulation_id: Optional[str] = None
    entity_types: List[str] = field(default_factory=list)
    profiles_count: int = 0
    tags: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "world_id": self.world_id,
            "name": self.name,
            "description": self.description,
            "audience_summary": self.audience_summary,
            "project_id": self.project_id,
            "graph_id": self.graph_id,
            "source_simulation_id": self.source_simulation_id,
            "entity_types": self.entity_types,
            "profiles_count": self.profiles_count,
            "tags": self.tags,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "World":
        return cls(
            world_id=data["world_id"],
            name=data.get("name", "Untitled audience"),
            description=data.get("description", ""),
            audience_summary=data.get("audience_summary", ""),
            project_id=data["project_id"],
            graph_id=data["graph_id"],
            source_simulation_id=data.get("source_simulation_id"),
            entity_types=data.get("entity_types", []),
            profiles_count=data.get("profiles_count", 0),
            tags=data.get("tags", []),
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
        )


class WorldManager:
    """Persists Worlds as one JSON file per World under uploads/worlds/."""

    WORLDS_DIR = os.path.join(Config.UPLOAD_FOLDER, "worlds")

    @classmethod
    def _ensure_dir(cls) -> None:
        os.makedirs(cls.WORLDS_DIR, exist_ok=True)

    @classmethod
    def _path(cls, world_id: str) -> str:
        return os.path.join(cls.WORLDS_DIR, f"{world_id}.json")

    @classmethod
    def create(
        cls,
        name: str,
        description: str,
        audience_summary: str,
        project_id: str,
        graph_id: str,
        source_simulation_id: Optional[str] = None,
        entity_types: Optional[List[str]] = None,
        profiles_count: int = 0,
        tags: Optional[List[str]] = None,
    ) -> World:
        cls._ensure_dir()
        world = World(
            world_id=f"world_{uuid.uuid4().hex[:12]}",
            name=name,
            description=description,
            audience_summary=audience_summary,
            project_id=project_id,
            graph_id=graph_id,
            source_simulation_id=source_simulation_id,
            entity_types=entity_types or [],
            profiles_count=profiles_count,
            tags=tags or [],
        )
        cls.save(world)
        return world

    @classmethod
    def save(cls, world: World) -> None:
        cls._ensure_dir()
        world.updated_at = datetime.now().isoformat()
        with open(cls._path(world.world_id), "w", encoding="utf-8") as f:
            json.dump(world.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def get(cls, world_id: str) -> Optional[World]:
        path = cls._path(world_id)
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return World.from_dict(json.load(f))

    @classmethod
    def list(cls) -> List[World]:
        cls._ensure_dir()
        worlds: List[World] = []
        for name in os.listdir(cls.WORLDS_DIR):
            if not name.endswith(".json"):
                continue
            try:
                with open(os.path.join(cls.WORLDS_DIR, name), "r", encoding="utf-8") as f:
                    worlds.append(World.from_dict(json.load(f)))
            except Exception:
                continue
        worlds.sort(key=lambda w: w.created_at, reverse=True)
        return worlds

    @classmethod
    def delete(cls, world_id: str) -> bool:
        path = cls._path(world_id)
        if not os.path.exists(path):
            return False
        os.remove(path)
        return True
