"""
Worlds API — manage reusable synthetic audiences and their variant runs.

A World snapshots an existing project + Zep graph + persona set so users can
fire new "what-if" prompts (variant runs) against the same audience without
rebuilding the expensive graph/persona stages.
"""

import os
import json
import traceback
from typing import Any, Dict, List, Optional

from flask import request, jsonify

from . import worlds_bp
from ..config import Config
from ..models.project import ProjectManager
from ..models.world import World, WorldManager
from ..services.simulation_manager import SimulationManager
from ..services.simulation_runner import SimulationRunner
from ..utils.logger import get_logger
from ..utils.locale import t

logger = get_logger('mirofish.api.worlds')


def _world_with_stats(world: World) -> Dict[str, Any]:
    """Attach derived stats (variant count, latest variant time) to a World dict."""
    data = world.to_dict()
    variants = _list_variants_for_world(world)
    data["variant_count"] = len(variants)
    data["latest_variant_at"] = variants[0]["created_at"] if variants else None
    return data


def _list_variants_for_world(world: World) -> List[Dict[str, Any]]:
    """All simulations under this World's project, newest first."""
    manager = SimulationManager()
    sims = manager.list_simulations(project_id=world.project_id)

    out: List[Dict[str, Any]] = []
    for sim in sims:
        sim_dict = sim.to_dict()
        # Pull per-variant prompt from the simulation's frozen config
        config = manager.get_simulation_config(sim.simulation_id)
        prompt = (config or {}).get("simulation_requirement", "") if config else ""

        run_state = SimulationRunner.get_run_state(sim.simulation_id)
        out.append({
            "simulation_id": sim.simulation_id,
            "status": sim_dict.get("status"),
            "prompt": prompt,
            "current_round": run_state.current_round if run_state else 0,
            "total_rounds": run_state.total_rounds if run_state else 0,
            "runner_status": run_state.runner_status.value if run_state else "idle",
            "report_id": _get_report_id_for_simulation(sim.simulation_id),
            "is_source": sim.simulation_id == world.source_simulation_id,
            "created_at": sim_dict.get("created_at"),
            "updated_at": sim_dict.get("updated_at"),
        })

    out.sort(key=lambda v: v.get("created_at") or "", reverse=True)
    return out


def _get_report_id_for_simulation(simulation_id: str) -> Optional[str]:
    """Find the latest report_id for a given simulation_id by scanning reports/."""
    reports_dir = os.path.join(Config.UPLOAD_FOLDER, 'reports')
    if not os.path.exists(reports_dir):
        return None

    matching: List[Dict[str, str]] = []
    try:
        for folder in os.listdir(reports_dir):
            meta_path = os.path.join(reports_dir, folder, "meta.json")
            if not os.path.exists(meta_path):
                continue
            try:
                with open(meta_path, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
            except Exception:
                continue
            if meta.get("simulation_id") == simulation_id:
                matching.append({
                    "report_id": meta.get("report_id"),
                    "created_at": meta.get("created_at", ""),
                })
        if not matching:
            return None
        matching.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return matching[0].get("report_id")
    except Exception as e:
        logger.warning(f"find report for sim {simulation_id} failed: {e}")
        return None


@worlds_bp.route('', methods=['GET'])
def list_worlds():
    """List all Worlds with derived stats."""
    try:
        worlds = WorldManager.list()
        return jsonify({
            "success": True,
            "data": [_world_with_stats(w) for w in worlds],
            "count": len(worlds),
        })
    except Exception as e:
        logger.error(f"list worlds failed: {e}")
        return jsonify({"success": False, "error": str(e), "traceback": traceback.format_exc()}), 500


@worlds_bp.route('', methods=['POST'])
def create_world():
    """
    Create a new World from an existing project + simulation.

    Body:
        {
          "name": "TechCo Q4 audience",
          "description": "...",
          "audience_summary": "...",
          "project_id": "proj_xxx",        // required
          "simulation_id": "sim_xxx",      // optional — its graph_id is used if project has none
          "tags": ["b2b", "us-enterprise"] // optional
        }
    """
    try:
        data = request.get_json() or {}
        project_id = data.get("project_id")
        if not project_id:
            return jsonify({"success": False, "error": "project_id is required"}), 400

        project = ProjectManager.get_project(project_id)
        if not project:
            return jsonify({"success": False, "error": t('api.projectNotFound', id=project_id)}), 404

        simulation_id = data.get("simulation_id")
        graph_id = project.graph_id
        entity_types: List[str] = []
        profiles_count = 0

        if simulation_id:
            sim_state = SimulationManager().get_simulation(simulation_id)
            if not sim_state:
                return jsonify({"success": False, "error": t('api.simulationNotFound', id=simulation_id)}), 404
            graph_id = graph_id or sim_state.graph_id
            entity_types = list(sim_state.entity_types or [])
            profiles_count = sim_state.profiles_count or 0

        if not graph_id:
            return jsonify({"success": False, "error": "project has no graph_id yet — build the graph first"}), 400

        name = (data.get("name") or project.name or "Untitled audience").strip()
        description = (data.get("description") or "").strip()
        audience_summary = (data.get("audience_summary") or project.analysis_summary or "").strip()
        tags = data.get("tags") or []

        world = WorldManager.create(
            name=name,
            description=description,
            audience_summary=audience_summary,
            project_id=project_id,
            graph_id=graph_id,
            source_simulation_id=simulation_id,
            entity_types=entity_types,
            profiles_count=profiles_count,
            tags=tags,
        )
        logger.info(f"world created: {world.world_id} from project={project_id} sim={simulation_id}")
        return jsonify({"success": True, "data": _world_with_stats(world)})
    except Exception as e:
        logger.error(f"create world failed: {e}")
        return jsonify({"success": False, "error": str(e), "traceback": traceback.format_exc()}), 500


@worlds_bp.route('/<world_id>', methods=['GET'])
def get_world(world_id: str):
    try:
        world = WorldManager.get(world_id)
        if not world:
            return jsonify({"success": False, "error": "world not found"}), 404
        return jsonify({"success": True, "data": _world_with_stats(world)})
    except Exception as e:
        logger.error(f"get world failed: {e}")
        return jsonify({"success": False, "error": str(e), "traceback": traceback.format_exc()}), 500


@worlds_bp.route('/<world_id>', methods=['PATCH'])
def update_world(world_id: str):
    """Update editable fields (name, description, audience_summary, tags)."""
    try:
        world = WorldManager.get(world_id)
        if not world:
            return jsonify({"success": False, "error": "world not found"}), 404
        data = request.get_json() or {}
        for field_name in ("name", "description", "audience_summary"):
            if field_name in data and isinstance(data[field_name], str):
                setattr(world, field_name, data[field_name].strip())
        if "tags" in data and isinstance(data["tags"], list):
            world.tags = data["tags"]
        WorldManager.save(world)
        return jsonify({"success": True, "data": _world_with_stats(world)})
    except Exception as e:
        logger.error(f"update world failed: {e}")
        return jsonify({"success": False, "error": str(e), "traceback": traceback.format_exc()}), 500


@worlds_bp.route('/<world_id>', methods=['DELETE'])
def delete_world(world_id: str):
    try:
        ok = WorldManager.delete(world_id)
        if not ok:
            return jsonify({"success": False, "error": "world not found"}), 404
        return jsonify({"success": True, "data": {"world_id": world_id, "deleted": True}})
    except Exception as e:
        logger.error(f"delete world failed: {e}")
        return jsonify({"success": False, "error": str(e), "traceback": traceback.format_exc()}), 500


@worlds_bp.route('/<world_id>/variants', methods=['GET'])
def list_variants(world_id: str):
    """List variant runs (simulations) attached to this World."""
    try:
        world = WorldManager.get(world_id)
        if not world:
            return jsonify({"success": False, "error": "world not found"}), 404
        variants = _list_variants_for_world(world)
        return jsonify({"success": True, "data": variants, "count": len(variants)})
    except Exception as e:
        logger.error(f"list variants failed: {e}")
        return jsonify({"success": False, "error": str(e), "traceback": traceback.format_exc()}), 500


@worlds_bp.route('/<world_id>/variants', methods=['POST'])
def create_variant(world_id: str):
    """
    Spin up a new variant run against this World.

    Reuses the World's project_id + graph_id (so graph + personas are free)
    and stores the new prompt on the project so /prepare picks it up.

    Body:
        {
          "prompt": "What if we launch on Black Friday with a 30% discount?",
          "enable_twitter": true,    // optional, default true
          "enable_reddit": true      // optional, default true
        }

    Returns:
        { simulation_id, project_id, world_id, status: "created" }
    The frontend then navigates to /simulation/:simulation_id to run prepare → start.
    """
    try:
        world = WorldManager.get(world_id)
        if not world:
            return jsonify({"success": False, "error": "world not found"}), 404

        data = request.get_json() or {}
        prompt = (data.get("prompt") or "").strip()
        if not prompt:
            return jsonify({"success": False, "error": "prompt is required"}), 400

        project = ProjectManager.get_project(world.project_id)
        if not project:
            return jsonify({"success": False, "error": t('api.projectNotFound', id=world.project_id)}), 404

        # Stamp the new prompt onto the project so the existing /prepare
        # pipeline picks it up. Each /prepare run snapshots the requirement
        # into the simulation's own simulation_config.json, so previous
        # variants' prompts are preserved per-sim.
        project.simulation_requirement = prompt
        ProjectManager.save_project(project)

        manager = SimulationManager()
        sim_state = manager.create_simulation(
            project_id=world.project_id,
            graph_id=world.graph_id,
            enable_twitter=bool(data.get("enable_twitter", True)),
            enable_reddit=bool(data.get("enable_reddit", True)),
        )

        logger.info(f"variant created for world {world_id}: sim={sim_state.simulation_id}")
        return jsonify({
            "success": True,
            "data": {
                "simulation_id": sim_state.simulation_id,
                "project_id": world.project_id,
                "graph_id": world.graph_id,
                "world_id": world_id,
                "status": sim_state.status.value,
                "prompt": prompt,
            },
        })
    except Exception as e:
        logger.error(f"create variant failed: {e}")
        return jsonify({"success": False, "error": str(e), "traceback": traceback.format_exc()}), 500
