"""Pytest hooks for artifacts/api-server."""

import os


def pytest_configure(config) -> None:  # noqa: ARG001
    # Milan PDF tests call render_* with lang=hi without bundling bundled Noto files.
    # Production MUST omit this — native-script PDFs require fonts under fonts/noto/.
    os.environ.setdefault("MILAN_PDF_RELAX_NATIVE_FONT_REQUIREMENT", "1")
