#!/usr/bin/env python3
"""Capture RC-1.2A screenshots via Playwright."""
from __future__ import annotations

import shutil
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:18083"
OUT = Path("/workspace/tests/artifacts/rc12a")
ART = Path("/opt/cursor/artifacts/screenshots")
OUT.mkdir(parents=True, exist_ok=True)
ART.mkdir(parents=True, exist_ok=True)


def save(page, name: str):
    path = OUT / name
    page.screenshot(path=str(path), full_page=True)
    shutil.copy(path, ART / name)
    print("saved", name)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, executable_path="/usr/local/bin/google-chrome")
        # Landing desktop
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(f"{BASE}/preview/landing", wait_until="networkidle")
        time.sleep(0.4)
        save(page, "landing_desktop.png")
        page.close()

        # Landing mobile
        page = browser.new_page(viewport={"width": 390, "height": 844})
        page.goto(f"{BASE}/preview/landing", wait_until="networkidle")
        time.sleep(0.3)
        save(page, "landing_mobile.png")
        page.close()

        # Ficha digital flow
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        page.goto(f"{BASE}/preview/ficha-digital", wait_until="networkidle")
        page.wait_for_function(
            "() => document.querySelectorAll('#fd-collab option').length > 0"
        )
        time.sleep(0.3)
        save(page, "send_form.png")

        page.click("#fd-send")
        page.wait_for_selector("#fd-open-employee", state="visible")
        time.sleep(0.4)
        page.click("#fd-open-employee")
        page.wait_for_selector("#fd-consent", state="attached")
        time.sleep(0.3)
        # employee_mobile
        page.set_viewport_size({"width": 390, "height": 844})
        time.sleep(0.2)
        save(page, "employee_mobile.png")

        page.check("#fd-consent")
        page.click("#fd-start")
        page.wait_for_selector("#fd-submit", state="attached")
        # fill fields
        selects = page.query_selector_all("#fd-emp-frame select")
        for sel in selects:
            opts = sel.query_selector_all("option")
            if len(opts) > 1:
                sel.select_option(index=len(opts) - 1)
        page.click("#fd-submit")
        page.wait_for_selector(".bm-fd-success", state="attached")
        time.sleep(0.4)
        save(page, "employee_success.png")

        page.set_viewport_size({"width": 1280, "height": 900})
        # ensure staff detail loaded after submit
        page.wait_for_timeout(600)
        page.click('[data-panel="panel-analysis"]')
        time.sleep(0.5)
        save(page, "analysis.png")

        page.click('[data-panel="panel-alerts"]')
        time.sleep(0.4)
        save(page, "alerts.png")

        page.click('[data-panel="panel-timeline"]')
        time.sleep(0.4)
        save(page, "timeline.png")

        page.click('[data-panel="panel-tracking"]')
        time.sleep(0.4)
        save(page, "tracking.png")

        browser.close()
    print("done")


if __name__ == "__main__":
    main()
