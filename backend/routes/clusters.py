"""
backend/routes/clusters.py
GET /api/clusters        — все кластеры (для инициализации)
GET /api/clusters/<id>   — информация об одном кластере
"""

from flask import Blueprint, jsonify
from data.cluster_data import CLUSTER_INFO, CLUSTER_TAGS

clusters_bp = Blueprint("clusters", __name__)


@clusters_bp.route("/api/clusters", methods=["GET"])
def get_all_clusters():
    result = []
    for cid, info in CLUSTER_INFO.items():
        tags = CLUSTER_TAGS.get(cid, ("", "", "", ""))
        desc = str(info.get("description", "") or "")
        result.append({
            "cid": cid,
            "name": info.get("name", ""),
            "description": desc,
            "descriptionShort": desc[:110] + "…" if len(desc) > 90 else desc,
            "techTagClass": tags[0],
            "techLabel": tags[1],
            "overworkTagClass": tags[2],
            "overworkLabel": tags[3],
        })
    return jsonify(result)


@clusters_bp.route("/api/clusters/<int:cluster_id>", methods=["GET"])
def get_cluster(cluster_id):
    info = CLUSTER_INFO.get(cluster_id)
    if not info:
        return jsonify({"error": "Cluster not found"}), 404
    tags = CLUSTER_TAGS.get(cluster_id, ("", "", "", ""))
    return jsonify({
        "cid": cluster_id,
        "name": info.get("name", ""),
        "description": info.get("description", ""),
        "techTagClass": tags[0],
        "techLabel": tags[1],
        "overworkTagClass": tags[2],
        "overworkLabel": tags[3],
    })
