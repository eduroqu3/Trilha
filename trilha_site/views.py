from pathlib import Path

from django.http import FileResponse
from django.shortcuts import render


BASE_DIR = Path(__file__).resolve().parent.parent


def landing_page(request):
    return render(request, "landing.html")


def route_manifest(request):
    return FileResponse(
        (BASE_DIR / "manus-routes.json").open("rb"),
        content_type="application/json",
    )
