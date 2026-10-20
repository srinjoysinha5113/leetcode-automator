import asyncio
import json
import re

import time
from typing import Optional, Tuple
from playwright.async_api import BrowserContext, Page, Response, async_playwright
from app.account_verifier import AccountVerifier
from app.config import logger, settings
from app.database import DatabaseManager
from app.models import SubmissionResult, Verdict, VerificationStatus

class LeetCodeSubmitter:
    """Automates and verifies LeetCode problem submissions through the official website."""

    def __init__(self, browser_profile_dir: Optional[str] = None):
        self.profile_dir = str(browser_profile_dir or settings.BROWSER_PROFILE_DIR)
        self.timeout = settings.SUBMISSION_TIMEOUT_SECONDS
        self.verifier = AccountVerifier(self.profile_dir)

    async def submit_solution(
        self,
        problem_slug: str,
        solution_code: str,
        attempt_id: Optional[int] = None,
        headless: Optional[bool] = None,
    ) -> SubmissionResult:
        """
        Submits code to LeetCode with account identity verification,
        DOM & network response monitoring, and terminal verdict polling.
        """
        if not settings.AUTO_SUBMIT:
            msg = "AUTO_SUBMIT is disabled in configuration. Real submission was skipped."
            logger.info(f"[{problem_slug}] {msg}")
            return SubmissionResult(
                verdict=Verdict.UNKNOWN,
                raw_output=msg,
                error=msg
            )

        # 1. Identity Check
        status, username, verify_msg = await self.verifier.verify_identity(headless=True)
        if status != VerificationStatus.VERIFIED:
            err = f"Account verification failed before submission: {verify_msg}"
            logger.error(err)
            return SubmissionResult(
                verdict=Verdict.UNKNOWN,
                error=err
            )

        run_headless = settings.BROWSER_HEADLESS if headless is None else headless

        async with async_playwright() as p:
            context: BrowserContext = await p.chromium.launch_persistent_context(
                user_data_dir=self.profile_dir,
                headless=run_headless,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
                viewport={"width": 1440, "height": 900},
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
            )
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            page = await context.new_page()

            submission_id: Optional[str] = None
            submission_check_data: dict = {}

            # Listen for network responses from LeetCode submit and check endpoints
            async def handle_response(response: Response):
                nonlocal submission_id, submission_check_data
                url = response.url
                try:
                    if "/submit/" in url and response.request.method == "POST":
                        data = await response.json()
                        if data and "submission_id" in data:
                            submission_id = str(data["submission_id"])
                            logger.info(f"[{problem_slug}] Captured submission ID: {submission_id}")
                    elif "/check/" in url and submission_id and submission_id in url:
                        data = await response.json()
                        if data:
                            submission_check_data = data
                except Exception:
                    pass

            page.on("response", handle_response)

            # Intercept submit POST request to enforce lang="python3" and solution_code
            async def handle_submit_route(route):
                req = route.request
                if "/submit/" in req.url and req.method == "POST":
                    try:
                        post_data = req.post_data_json
                        if post_data:
                            changed = False
                            if post_data.get("lang") != "python3":
                                logger.info(f"[{problem_slug}] Forcing submit language from '{post_data.get('lang')}' to 'python3'")
                                post_data["lang"] = "python3"
                                changed = True
                            if post_data.get("typed_code") != solution_code:
                                logger.info(f"[{problem_slug}] Enforcing verified solution_code in submit payload")
                                post_data["typed_code"] = solution_code
                                changed = True
                            if changed:
                                await route.continue_(post_data=json.dumps(post_data))
                                return
                    except Exception as e:
                        logger.warning(f"[{problem_slug}] Route interception error: {e}")
                await route.continue_()

            await page.route("**/submit/**", handle_submit_route)

            try:
                # 2. Navigate to problem page
                target_url = f"https://leetcode.com/problems/{problem_slug}/"
                logger.info(f"Navigating to {target_url}...")
                await page.goto(target_url, wait_until="domcontentloaded", timeout=45000)

                # Check for Cloudflare challenge
                title = await page.title()
                if "just a moment" in title.lower():
                    logger.warning(f"[{problem_slug}] Cloudflare challenge detected ('{title}'). Waiting up to 15s...")
                    for _ in range(15):
                        await asyncio.sleep(1)
                        title = await page.title()
                        if "just a moment" not in title.lower():
                            logger.info(f"[{problem_slug}] Cloudflare challenge resolved. Title: '{title}'")
                            break
                    if "just a moment" in title.lower():
                        err = (
                            "LeetCode page is blocked by Cloudflare verification ('Just a moment...'). "
                            "Please ensure BROWSER_HEADLESS=false in .env or solve verification in headed mode."
                        )
                        logger.error(err)
                        return SubmissionResult(verdict=Verdict.UNKNOWN, error=err)

                # Validate URL matches problem slug
                current_url = page.url
                if problem_slug not in current_url:
                    err = f"Navigation failed: current URL '{current_url}' does not match slug '{problem_slug}'"
                    logger.error(err)
                    return SubmissionResult(verdict=Verdict.UNKNOWN, error=err)

                # Ensure language is Python3 in UI
                try:
                    await page.evaluate("""() => {
                        try {
                            localStorage.setItem('global_lang', 'python3');
                            localStorage.setItem('preferred_editor_language', 'python3');
                        } catch(e) {}
                    }""")
                    lang_btn_selectors = [
                        'button[id^="headlessui-listbox-button"]',
                        'button[aria-haspopup="listbox"]',
                        'button:has-text("C++")',
                        'button:has-text("Java")',
                        'button:has-text("C#")',
                        'button:has-text("JavaScript")',
                        'button:has-text("TypeScript")',
                        'button:has-text("Go")',
                        'button:has-text("Rust")',
                    ]
                    for sel in lang_btn_selectors:
                        btn = await page.query_selector(sel)
                        if btn and await btn.is_visible():
                            txt = (await btn.inner_text()).strip()
                            if "python" not in txt.lower():
                                logger.info(f"[{problem_slug}] Switching language from '{txt}' to Python3...")
                                await btn.click()
                                await asyncio.sleep(0.5)
                                opts = await page.query_selector_all('[role="option"], li, div[role="menuitem"]')
                                for opt in opts:
                                    opt_txt = (await opt.inner_text()).strip()
                                    if opt_txt in ("Python3", "Python 3", "Python"):
                                        await opt.click()
                                        logger.info(f"[{problem_slug}] Selected Python3.")
                                        await asyncio.sleep(1)
                                        break
                            break
                except Exception as e:
                    logger.debug(f"[{problem_slug}] Language switcher hint: {e}")

                # 3. Populate Monaco Editor - wait dynamically for the code model to hydrate
                logger.info(f"[{problem_slug}] Waiting for Monaco code model to initialize...")
                try:
                    await page.wait_for_function(
                        """() => {
                            const models = window.monaco?.editor?.getModels();
                            if (!models || models.length === 0) return false;
                            const codeModel = models.find(m => m.getLanguageId() !== 'plaintext' || m.getValue().length > 0);
                            return Boolean(codeModel);
                        }""",
                        timeout=15000
                    )
                except Exception:
                    pass

                # Short pause to ensure React hydration has finished updating the model
                await asyncio.sleep(1)

                editor_set = await page.evaluate(
                    """
                    (code) => {
                        try {
                            const models = window.monaco?.editor?.getModels();
                            if (models && models.length > 0) {
                                const target = models.find(m => m.getLanguageId() !== 'plaintext') || models[0];
                                target.setValue(code);
                                return true;
                            }
                            return false;
                        } catch (e) {
                            return false;
                        }
                    }
                    """,
                    solution_code
                )

                if not editor_set:
                    # Fallback: wait for .monaco-editor DOM element and type/paste
                    try:
                        editor_el = await page.wait_for_selector('.monaco-editor', timeout=10000)
                    except Exception:
                        editor_el = None

                    if editor_el:
                        await editor_el.click()
                        await page.keyboard.press("Control+A")
                        await page.keyboard.press("Backspace")
                        await page.keyboard.insert_text(solution_code)
                        editor_set = True
                    else:
                        err = "Monaco editor could not be located or populated on the problem page."
                        logger.error(err)
                        return SubmissionResult(verdict=Verdict.UNKNOWN, error=err)

                await asyncio.sleep(1)

                # 4. Locate and click Submit button
                submit_selectors = [
                    'button[data-e2e-locator="console-submit-button"]',
                    'button:has-text("Submit")',
                    '[data-cy="submit-code-btn"]',
                ]
                submit_btn = None
                for sel in submit_selectors:
                    btn = await page.query_selector(sel)
                    if btn and await btn.is_visible():
                        submit_btn = btn
                        break

                if not submit_btn:
                    err = "Submit button could not be located. LeetCode layout may have changed."
                    logger.error(err)
                    return SubmissionResult(verdict=Verdict.UNKNOWN, error=err)

                logger.info(f"[{problem_slug}] Clicking Submit button...")
                await submit_btn.click()

                # 5. Wait for terminal verdict (via network check responses or DOM result panel)
                start_wait = time.time()
                verdict = Verdict.UNKNOWN
                runtime_ms = None
                memory_mb = None
                raw_text = ""

                while time.time() - start_wait < self.timeout:
                    # Check network API data first (highest accuracy)
                    if submission_check_data.get("state") == "SUCCESS":
                        status_msg = submission_check_data.get("status_msg", "")
                        raw_text = str(submission_check_data)

                        if status_msg == "Accepted":
                            verdict = Verdict.ACCEPTED
                        elif status_msg == "Wrong Answer":
                            verdict = Verdict.WRONG_ANSWER
                        elif "Time Limit" in status_msg:
                            verdict = Verdict.TIME_LIMIT_EXCEEDED
                        elif "Runtime Error" in status_msg:
                            verdict = Verdict.RUNTIME_ERROR
                        elif "Compile Error" in status_msg:
                            verdict = Verdict.COMPILE_ERROR
                        elif "Memory Limit" in status_msg:
                            verdict = Verdict.MEMORY_LIMIT_EXCEEDED
                        else:
                            verdict = Verdict.UNKNOWN

                        # Extract metrics
                        runtime_str = submission_check_data.get("status_runtime", "")
                        mem_str = submission_check_data.get("status_memory", "")
                        r_match = re.search(r"(\d+)\s*ms", runtime_str)
                        if r_match:
                            runtime_ms = int(r_match.group(1))
                        m_match = re.search(r"([\d\.]+)\s*MB", mem_str)
                        if m_match:
                            memory_mb = float(m_match.group(1))

                        break

                    # Check DOM result container as secondary source
                    result_containers = await page.query_selector_all('[data-e2e-locator="submission-result"], [data-cy="submission-result"]')
                    for rc in result_containers:
                        text = await rc.inner_text()
                        if "Accepted" in text:
                            verdict = Verdict.ACCEPTED
                            raw_text = text
                            break
                        elif "Wrong Answer" in text:
                            verdict = Verdict.WRONG_ANSWER
                            raw_text = text
                            break
                        elif "Time Limit Exceeded" in text:
                            verdict = Verdict.TIME_LIMIT_EXCEEDED
                            raw_text = text
                            break
                        elif "Runtime Error" in text:
                            verdict = Verdict.RUNTIME_ERROR
                            raw_text = text
                            break
                        elif "Compile Error" in text:
                            verdict = Verdict.COMPILE_ERROR
                            raw_text = text
                            break

                    if verdict != Verdict.UNKNOWN:
                        break

                    await asyncio.sleep(2)

                if verdict == Verdict.UNKNOWN and not raw_text:
                    verdict = Verdict.PENDING
                    raw_text = f"Submission timed out after {self.timeout}s waiting for verdict."

                # Record in database
                DatabaseManager.record_submission(
                    problem_slug=problem_slug,
                    attempt_id=attempt_id,
                    submission_id=submission_id,
                    verdict=verdict,
                    runtime_ms=runtime_ms,
                    memory_mb=memory_mb,
                    raw_verdict_text=raw_text,
                )

                logger.info(f"[{problem_slug}] Final submission verdict: {verdict.value} (ID: {submission_id})")
                return SubmissionResult(
                    submission_id=submission_id,
                    verdict=verdict,
                    runtime_ms=runtime_ms,
                    memory_mb=memory_mb,
                    raw_output=raw_text,
                )

            except Exception as e:
                err = f"Submission exception for {problem_slug}: {e}"
                logger.error(err)
                return SubmissionResult(verdict=Verdict.UNKNOWN, error=err)
            finally:
                await context.close()
