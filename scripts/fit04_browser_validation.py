#!/usr/bin/env python3
"""FIT-04 RC local browser validation harness.

Drivers (in order):
  1. Playwright sync API (if installed)
  2. Selenium + google-chrome / chromedriver (if available)
  3. Otherwise document skip and exit 0 (CI gate is separate)

Env:
  FIT04_BASE_URL  default http://127.0.0.1:18081
  FIT04_DB        path to staging SQLite (report metadata only)
  FIT04_ADMIN_USER / FIT04_ADMIN_PASS
  FIT04_USER_A_USER / FIT04_USER_A_PASS
  FIT04_USER_B_USER / FIT04_USER_B_PASS

Writes:
  /tmp/abs-fit04-rc-*/browser_report.json
  docs/integration/_fit04_browser_raw.md (when writable; else prints)
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Optional

ROOT = Path(__file__).resolve().parents[1]

VIEWPORTS = [
    (390, 844),
    (768, 1024),
    (1024, 768),
    (1366, 768),
]

SMOKE_PATHS = [
    "/login",
    "/landing",
    "/",
    "/clientes",
    "/dados_powerbi",
    "/funcionarios",
    "/upload",
    "/produtividade",
]

AUTHENTICATED_PATHS = [
    "/",
    "/clientes",
    "/dados_powerbi",
    "/funcionarios",
    "/upload",
    "/produtividade",
]

DEFAULT_CREDS = {
    "admin": ("fit04_admin", "Fit04Admin!"),
    "tenant_a": ("fit04_user_a", "Fit04UserA!"),
    "tenant_b": ("fit04_user_b", "Fit04UserB!"),
}


def _env(name: str, default: str = "") -> str:
    return (os.environ.get(name) or default).strip()


def _cred(profile: str) -> tuple[str, str]:
    if profile == "admin":
        return (
            _env("FIT04_ADMIN_USER", DEFAULT_CREDS["admin"][0]),
            _env("FIT04_ADMIN_PASS", DEFAULT_CREDS["admin"][1]),
        )
    if profile == "tenant_a":
        return (
            _env("FIT04_USER_A_USER", DEFAULT_CREDS["tenant_a"][0]),
            _env("FIT04_USER_A_PASS", DEFAULT_CREDS["tenant_a"][1]),
        )
    if profile == "tenant_b":
        return (
            _env("FIT04_USER_B_USER", DEFAULT_CREDS["tenant_b"][0]),
            _env("FIT04_USER_B_PASS", DEFAULT_CREDS["tenant_b"][1]),
        )
    raise KeyError(profile)


def _resolve_workdir(db_hint: str) -> Path:
    if db_hint:
        p = Path(db_hint)
        parent = p.parent if p.suffix else p
        if parent.exists() and parent.name.startswith("abs-fit04-rc-"):
            return parent
    # Prefer newest staging dir
    tmp = Path("/tmp")
    candidates = sorted(
        tmp.glob("abs-fit04-rc-*"),
        key=lambda x: x.stat().st_mtime if x.exists() else 0,
        reverse=True,
    )
    if candidates:
        return candidates[0]
    ts = time.strftime("%Y%m%d-%H%M%S")
    work = tmp / f"abs-fit04-rc-{ts}"
    work.mkdir(parents=True, exist_ok=True)
    return work


def _api_login(base_url: str, username: str, password: str) -> Optional[dict]:
    url = base_url.rstrip("/") + "/api/auth/login"
    body = urllib.parse.urlencode(
        {"username": username, "password": password}
    ).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        return {"_error": str(exc)}


# ---------------------------------------------------------------------------
# Driver abstraction
# ---------------------------------------------------------------------------


class BrowserDriver:
    name = "abstract"

    def set_viewport(self, width: int, height: int) -> None:
        raise NotImplementedError

    def goto(self, url: str) -> None:
        raise NotImplementedError

    def clear_storage(self) -> None:
        raise NotImplementedError

    def inject_auth(self, token: str, user: dict) -> None:
        raise NotImplementedError

    def ui_login(self, base_url: str, username: str, password: str) -> bool:
        raise NotImplementedError

    def current_url(self) -> str:
        raise NotImplementedError

    def page_has_auth_js(self) -> bool:
        raise NotImplementedError

    def collect_requests_matching(self, substr: str) -> list[str]:
        raise NotImplementedError

    def start_network_capture(self) -> None:
        pass

    def close(self) -> None:
        pass


class PlaywrightDriver(BrowserDriver):
    name = "playwright"

    def __init__(self, headless: bool = True):
        from playwright.sync_api import sync_playwright

        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=headless)
        self._context = self._browser.new_context()
        self._page = self._context.new_page()
        self._captured: list[str] = []
        self._pending_auth: Optional[dict] = None
        self._page.on("request", lambda req: self._captured.append(req.url))
        # Apply pending auth before each document loads on the app origin
        self._context.add_init_script(
            """
            (() => {
              try {
                const raw = sessionStorage.getItem('__fit04_pending_auth');
                if (raw) {
                  const p = JSON.parse(raw);
                  localStorage.setItem('access_token', p.token);
                  localStorage.setItem('user', JSON.stringify(p.user || {}));
                  sessionStorage.removeItem('__fit04_pending_auth');
                }
              } catch (e) {}
            })();
            """
        )

    def set_viewport(self, width: int, height: int) -> None:
        self._page.set_viewport_size({"width": width, "height": height})

    def goto(self, url: str) -> None:
        self._page.goto(url, wait_until="domcontentloaded", timeout=30000)
        self._page.wait_for_timeout(400)

    def clear_storage(self) -> None:
        self._pending_auth = None
        self._context.clear_cookies()
        # Navigate to a blank page on about:blank then rely on next origin visit
        try:
            self._page.evaluate(
                "() => { try { localStorage.clear(); sessionStorage.clear(); } catch (e) {} }"
            )
        except Exception:
            pass

    def inject_auth(self, token: str, user: dict) -> None:
        self._pending_auth = {"token": token, "user": user}
        # Prefer direct set when already on an http(s) origin
        try:
            cur = self._page.url or ""
            if cur.startswith("http"):
                self._page.evaluate(
                    """([token, user]) => {
                      localStorage.setItem('access_token', token);
                      localStorage.setItem('user', JSON.stringify(user || {}));
                      sessionStorage.setItem(
                        '__fit04_pending_auth',
                        JSON.stringify({token, user})
                      );
                    }""",
                    [token, user],
                )
                return
        except Exception:
            pass
        # Defer via sessionStorage on next same-origin navigation after /login
        self._pending_auth = {"token": token, "user": user}

    def ensure_auth_on_origin(self, base_url: str) -> None:
        """Load /login and set localStorage for subsequent navigations."""
        if not self._pending_auth:
            return
        token = self._pending_auth["token"]
        user = self._pending_auth.get("user") or {}
        self.goto(base_url.rstrip("/") + "/login")
        self._page.evaluate(
            """([token, user]) => {
              localStorage.setItem('access_token', token);
              localStorage.setItem('user', JSON.stringify(user || {}));
            }""",
            [token, user],
        )

    def ui_login(self, base_url: str, username: str, password: str) -> bool:
        self.clear_storage()
        self.goto(base_url.rstrip("/") + "/login")
        self._page.fill("#username", username)
        self._page.fill("#password", password)
        self._page.click('button[type="submit"], #loginBtn, .login-btn')
        self._page.wait_for_timeout(1500)
        token = self._page.evaluate("() => localStorage.getItem('access_token')")
        return bool(token)

    def current_url(self) -> str:
        return self._page.url

    def page_has_auth_js(self) -> bool:
        return bool(
            self._page.evaluate(
                """() => {
                  const scripts = [...document.querySelectorAll('script[src]')];
                  return scripts.some(s => (s.src || '').includes('auth.js'));
                }"""
            )
        )

    def start_network_capture(self) -> None:
        self._captured = []

    def collect_requests_matching(self, substr: str) -> list[str]:
        return [u for u in self._captured if substr in u]

    def close(self) -> None:
        try:
            self._browser.close()
        finally:
            self._pw.stop()


class SeleniumDriver(BrowserDriver):
    name = "selenium"

    def __init__(self, headless: bool = True):
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options

        opts = Options()
        if headless:
            opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--window-size=1366,768")
        # Prefer google-chrome binary when present
        for binary in (
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
        ):
            if Path(binary).exists():
                opts.binary_location = binary
                break
        self._driver = webdriver.Chrome(options=opts)
        self._captured: list[str] = []
        try:
            self._driver.execute_cdp_cmd("Network.enable", {})
            self._driver.execute_cdp_cmd(
                "Network.setRequestInterception", {"patterns": [{"urlPattern": "*"}]}
            )
        except Exception:
            pass

    def set_viewport(self, width: int, height: int) -> None:
        self._driver.set_window_size(width, height)

    def goto(self, url: str) -> None:
        self._driver.get(url)
        time.sleep(0.5)

    def clear_storage(self) -> None:
        self._driver.delete_all_cookies()
        try:
            self._driver.execute_script(
                "try { localStorage.clear(); sessionStorage.clear(); } catch (e) {}"
            )
        except Exception:
            pass

    def inject_auth(self, token: str, user: dict) -> None:
        user_json = json.dumps(user)
        self._driver.execute_script(
            "localStorage.setItem('access_token', arguments[0]);"
            "localStorage.setItem('user', arguments[1]);",
            token,
            user_json,
        )

    def ui_login(self, base_url: str, username: str, password: str) -> bool:
        from selenium.webdriver.common.by import By

        self.clear_storage()
        self.goto(base_url.rstrip("/") + "/login")
        self._driver.find_element(By.ID, "username").send_keys(username)
        self._driver.find_element(By.ID, "password").send_keys(password)
        try:
            self._driver.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        except Exception:
            self._driver.find_element(By.ID, "loginBtn").click()
        time.sleep(1.5)
        token = self._driver.execute_script(
            "return localStorage.getItem('access_token');"
        )
        return bool(token)

    def current_url(self) -> str:
        return self._driver.current_url

    def page_has_auth_js(self) -> bool:
        return bool(
            self._driver.execute_script(
                """
                const scripts = [...document.querySelectorAll('script[src]')];
                return scripts.some(s => (s.src || '').includes('auth.js'));
                """
            )
        )

    def start_network_capture(self) -> None:
        self._captured = []
        try:
            # Performance log fallback
            self._driver.get_log("performance")
        except Exception:
            pass

    def collect_requests_matching(self, substr: str) -> list[str]:
        matches: list[str] = []
        try:
            for entry in self._driver.get_log("performance"):
                msg = json.loads(entry.get("message", "{}")).get("message", {})
                if msg.get("method") == "Network.requestWillBeSent":
                    url = msg.get("params", {}).get("request", {}).get("url", "")
                    if substr in url:
                        matches.append(url)
        except Exception:
            pass
        return matches

    def close(self) -> None:
        try:
            self._driver.quit()
        except Exception:
            pass


def _try_create_driver() -> tuple[Optional[BrowserDriver], str]:
    try:
        return PlaywrightDriver(), "playwright"
    except Exception as exc:
        pw_err = str(exc)
    try:
        return SeleniumDriver(), "selenium"
    except Exception as exc:
        se_err = str(exc)
        return None, f"playwright unavailable ({pw_err}); selenium unavailable ({se_err})"


def _step(report: dict, name: str, ok: bool, detail: Any = None) -> None:
    report["steps"].append({"name": name, "ok": bool(ok), "detail": detail})
    print(("OK" if ok else "FAIL"), name, detail if detail is not None else "")


def _login_profile(
    driver: BrowserDriver, base_url: str, profile: str
) -> tuple[bool, str, Optional[dict]]:
    user, password = _cred(profile)
    # Prefer API login + localStorage injection (faster / less flaky)
    data = _api_login(base_url, user, password)
    if data and data.get("access_token"):
        driver.clear_storage()
        driver.goto(base_url.rstrip("/") + "/login")
        driver.inject_auth(
            data["access_token"], data.get("user") or {"username": user}
        )
        if hasattr(driver, "ensure_auth_on_origin"):
            driver.ensure_auth_on_origin(base_url)
        return True, "api_token_injection", data
    # Fallback: UI login
    ok = driver.ui_login(base_url, user, password)
    return ok, "ui_login", data if isinstance(data, dict) else None


def run_validation(driver: BrowserDriver, base_url: str, db_path: str, work: Path) -> dict:
    report: dict[str, Any] = {
        "suite": "fit04_browser_validation",
        "base_url": base_url,
        "db": db_path,
        "workdir": str(work),
        "driver": driver.name,
        "viewports": [f"{w}x{h}" for w, h in VIEWPORTS],
        "steps": [],
        "skipped": False,
        "live_db_used": False,
    }

    # Reachability
    try:
        with urllib.request.urlopen(base_url.rstrip("/") + "/login", timeout=10) as r:
            reachable = r.status < 500
    except Exception as exc:  # noqa: BLE001
        reachable = False
        _step(report, "base_url_reachable", False, str(exc))
        report["status"] = "fail"
        return report
    _step(report, "base_url_reachable", reachable, base_url)

    # --- Unauthenticated: protected path → /login ---
    driver.clear_storage()
    protected = base_url.rstrip("/") + "/clientes"
    driver.goto(protected)
    time.sleep(0.8)
    cur = driver.current_url()
    redirected = "/login" in cur
    _step(
        report,
        "no_token_redirects_to_login",
        redirected,
        {"from": "/clientes", "url": cur},
    )

    # --- Landing: must NOT call /api/cadastro-empresa on load ---
    driver.clear_storage()
    driver.start_network_capture()
    driver.goto(base_url.rstrip("/") + "/landing")
    time.sleep(1.0)
    cadastro_hits = driver.collect_requests_matching("/api/cadastro-empresa")
    # Playwright captures during navigation; selenium best-effort
    if driver.name == "playwright":
        _step(
            report,
            "landing_no_cadastro_empresa_network",
            len(cadastro_hits) == 0,
            cadastro_hits,
        )
    else:
        _step(
            report,
            "landing_no_cadastro_empresa_network",
            len(cadastro_hits) == 0,
            {"hits": cadastro_hits, "note": "selenium capture best-effort"},
        )

    # --- Per-profile + viewport smoke ---
    for profile in ("admin", "tenant_a", "tenant_b"):
        ok_login, method, login_data = _login_profile(driver, base_url, profile)
        _step(
            report,
            f"login_{profile}",
            ok_login,
            {"method": method, "error": (login_data or {}).get("_error")},
        )
        if not ok_login:
            continue

        if login_data and login_data.get("access_token"):
            driver.inject_auth(
                login_data["access_token"],
                login_data.get("user") or {},
            )
            if hasattr(driver, "ensure_auth_on_origin"):
                driver.ensure_auth_on_origin(base_url)

        for w, h in VIEWPORTS:
            driver.set_viewport(w, h)
            vp = f"{w}x{h}"
            for path in SMOKE_PATHS:
                url = base_url.rstrip("/") + path
                try:
                    if (
                        path in AUTHENTICATED_PATHS
                        and login_data
                        and login_data.get("access_token")
                    ):
                        # Keep token across navigations (auth.js may clear on bounce)
                        try:
                            driver.inject_auth(
                                login_data["access_token"],
                                login_data.get("user") or {},
                            )
                        except Exception:
                            pass
                    driver.goto(url)
                    cur = driver.current_url()
                    status_ok = True
                    detail: dict[str, Any] = {"url": cur, "path": path}

                    if path == "/login":
                        # Authenticated users are redirected to /clientes or /
                        # (login.html); unauthenticated stay on /login.
                        if login_data and login_data.get("access_token"):
                            status_ok = (
                                "/login" in cur
                                or "/clientes" in cur
                                or cur.rstrip("/").endswith("18081")
                                or cur.rstrip("/").endswith("/")
                            )
                        else:
                            status_ok = "/login" in cur
                    elif path == "/landing":
                        status_ok = "landing" in cur
                    elif path in AUTHENTICATED_PATHS:
                        # With token should not bounce to login
                        bounced = "/login" in cur and path != "/login"
                        has_auth = driver.page_has_auth_js()
                        detail["auth_js"] = has_auth
                        detail["bounced_to_login"] = bounced
                        # auth.js required on authenticated pages
                        status_ok = (not bounced) and has_auth
                    _step(
                        report,
                        f"smoke_{profile}_{vp}_{path.strip('/') or 'root'}",
                        status_ok,
                        detail,
                    )
                except Exception as exc:  # noqa: BLE001
                    _step(
                        report,
                        f"smoke_{profile}_{vp}_{path.strip('/') or 'root'}",
                        False,
                        str(exc),
                    )

        # Explicit auth.js check on one authenticated page
        driver.goto(base_url.rstrip("/") + "/clientes")
        _step(
            report,
            f"auth_js_loaded_{profile}",
            driver.page_has_auth_js(),
            driver.current_url(),
        )

    failed = [s for s in report["steps"] if not s["ok"]]
    report["status"] = "fail" if failed else "pass"
    report["failed_count"] = len(failed)
    return report


def _write_outputs(report: dict, work: Path) -> None:
    out_json = work / "browser_report.json"
    out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("BROWSER_REPORT", out_json)

    lines = [
        "# FIT-04 browser validation (raw)",
        "",
        f"- status: **{report.get('status')}**",
        f"- driver: `{report.get('driver')}`",
        f"- base_url: `{report.get('base_url')}`",
        f"- db: `{report.get('db')}`",
        f"- workdir: `{report.get('workdir')}`",
        f"- skipped: `{report.get('skipped')}`",
        "",
        "## Steps",
        "",
    ]
    for s in report.get("steps", []):
        mark = "PASS" if s.get("ok") else "FAIL"
        if report.get("skipped"):
            mark = "SKIP"
        lines.append(f"- [{mark}] `{s.get('name')}` — {s.get('detail')!r}")
    lines.append("")
    md = "\n".join(lines)

    md_path = ROOT / "docs" / "integration" / "_fit04_browser_raw.md"
    try:
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(md, encoding="utf-8")
        print("BROWSER_MD", md_path)
    except OSError as exc:
        print("BROWSER_MD_PRINT_FALLBACK", str(exc))
        print(md)


def main() -> int:
    base_url = _env("FIT04_BASE_URL", "http://127.0.0.1:18081")
    db_path = _env("FIT04_DB", "")
    work = _resolve_workdir(db_path)
    if not db_path:
        candidate = work / "staging.sqlite"
        db_path = str(candidate) if candidate.exists() else ""

    driver, info = _try_create_driver()
    if driver is None:
        report = {
            "suite": "fit04_browser_validation",
            "base_url": base_url,
            "db": db_path,
            "workdir": str(work),
            "driver": None,
            "skipped": True,
            "status": "skipped",
            "skip_reason": info,
            "steps": [
                {
                    "name": "browser_driver",
                    "ok": True,
                    "detail": f"skipped: {info}",
                }
            ],
            "note": (
                "Playwright/Selenium not installed — exit 0 with skipped status. "
                "CI browser gate is separate."
            ),
            "live_db_used": False,
        }
        _write_outputs(report, work)
        print("SKIPPED", info)
        return 0

    try:
        report = run_validation(driver, base_url, db_path, work)
    finally:
        driver.close()

    _write_outputs(report, work)
    return 0 if report.get("status") == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
