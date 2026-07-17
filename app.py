from nicegui import ui

from core import create_studio_core
from ui.dashboard import build_dashboard

studio = create_studio_core()
build_dashboard(studio)

ui.run(
    title="AI Movie Studio",
    reload=True,
)