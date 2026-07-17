"""Service boundary for production health and reusable project assets."""

from movie.asset_manager import AssetManager
from movie.production_manager import ProductionManager


class ProductionService:
    status = staticmethod(ProductionManager.get_status)
    statistics = staticmethod(ProductionManager.get_statistics)
    health = staticmethod(ProductionManager.get_health)
    missing_assets = staticmethod(ProductionManager.get_missing_assets)
    ensure_structure = staticmethod(ProductionManager.ensure_structure)


class AssetService:
    list = staticmethod(AssetManager.list)
    save = staticmethod(AssetManager.save)
    delete = staticmethod(AssetManager.delete)
