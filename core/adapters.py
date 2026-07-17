"""Backwards-compatible adapters around the proven movie-layer managers."""
from __future__ import annotations

from movie.asset_manager import AssetManager
from movie.capability_manager import CapabilityManager
from movie.production_manager import ProductionManager


class AssetManagerAdapter:
    list = staticmethod(AssetManager.list)
    save = staticmethod(AssetManager.save)
    delete = staticmethod(AssetManager.delete)


class ProductionManagerAdapter:
    ensure_structure = staticmethod(ProductionManager.ensure_structure)
    get_status = staticmethod(ProductionManager.get_status)
    get_statistics = staticmethod(ProductionManager.get_statistics)
    get_health = staticmethod(ProductionManager.get_health)
    get_missing_assets = staticmethod(ProductionManager.get_missing_assets)


class CapabilityManagerAdapter:
    inspect = staticmethod(CapabilityManager.inspect)
