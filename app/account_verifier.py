import asyncio
import time
from typing import Optional, Tuple
from playwright.async_api import BrowserContext, Page, async_playwright
from app.config import logger, settings
from app.database import DatabaseManager
from app.models import VerificationStatus

GRAPHQL_USER_STATUS_QUERY = """
query {
  userStatus {
    isSignedIn
    username
    userSlug
  }
}
"""

class AccountVerifier:
    """Verifies LeetCode authenticated user identity using Playwright persistent browser context."""

    def __init__(self, browser_profile_dir: Optional[str] = None):
        self.profile_dir = str(browser_profile_dir or settings.BROWSER_PROFILE_DIR)
        self.expected_username = (settings.EXPECTED_LEETCODE_USERNAME or "").strip()

    async def get_active_username(self, page: Page) -> Tuple[bool, Optional[str]]:
        """
        Retrieves the signed-in username from page context using LeetCode's in-browser GraphQL endpoint
        or DOM elements. Does not access or log raw session cookies.
        """
        try:
            # 1. Attempt in-page GraphQL call with browser session cookies
            user_status = await page.evaluate(
                """
                async () => {
                    try {
                        const resp = await fetch('/graphql', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                query: '{ userStatus { isSignedIn username userSlug } }'
                            })
                        });
                        const data = await resp.json();
                        return data?.data?.userStatus || null;
                    } catch (e) {
                        return null;
                    }
                }
                """
            )

            if user_status and user_status.get("isSignedIn"):
                username = user_status.get("username") or user_status.get("userSlug")
                if username:
                    return True, username

            # 2. Fallback to DOM inspection
            profile_selectors = [
                'a[href*="/profile/"]',
                'a[href*="/u/"]',
                '[data-cy="user-avatar"]',
                '#navbar_user_avatar',
            ]
            for sel in profile_selectors:
                el = await page.query_selector(sel)
                if el:
                    href = await el.get_attribute("href")
                    if href:
                        parts = [p for p in href.split("/") if p]
                        if parts:
                            return True, parts[-1]

            return False, None
        except Exception as e:
            logger.debug(f"Failed to extract username from page: {e}")
            return False, None

    async def verify_identity(self, headless: bool = True) -> Tuple[VerificationStatus, Optional[str], str]:
        """
        Performs strict identity verification against EXPECTED_LEETCODE_USERNAME.
        Returns: (VerificationStatus, retrieved_username, message)
        """
        if not self.expected_username:
            msg = "EXPECTED_LEETCODE_USERNAME is not configured in .env. Submissions disabled."
            logger.error(msg)
            DatabaseManager.record_account_verification(
                username=None,
                expected_username="",
                status=VerificationStatus.UNVERIFIABLE,
                details=msg
            )
            return VerificationStatus.UNVERIFIABLE, None, msg

        async with async_playwright() as p:
            context: BrowserContext = await p.chromium.launch_persistent_context(
                user_data_dir=self.profile_dir,
                headless=headless,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800},
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
            )
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            try:
                page = await context.new_page()
                await page.goto("https://leetcode.com", wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(2)

                is_signed_in, username = await self.get_active_username(page)

                if not is_signed_in or not username:
                    msg = "No authenticated LeetCode session found. Please run 'python main.py verify-account' to log in."
                    logger.warning(msg)
                    DatabaseManager.record_account_verification(
                        username=None,
                        expected_username=self.expected_username,
                        status=VerificationStatus.NOT_LOGGED_IN,
                        details=msg
                    )
                    return VerificationStatus.NOT_LOGGED_IN, None, msg

                if username.lower() != self.expected_username.lower():
                    msg = (
                        f"Account mismatch: Logged-in username '{username}' does not match "
                        f"EXPECTED_LEETCODE_USERNAME '{self.expected_username}' in .env. Submissions strictly disabled."
                    )
                    logger.error(msg)
                    DatabaseManager.record_account_verification(
                        username=username,
                        expected_username=self.expected_username,
                        status=VerificationStatus.MISMATCH,
                        details=msg
                    )
                    return VerificationStatus.MISMATCH, username, msg

                success_msg = f"Account verified successfully. Logged-in user: '{username}'."
                logger.info(success_msg)
                DatabaseManager.record_account_verification(
                    username=username,
                    expected_username=self.expected_username,
                    status=VerificationStatus.VERIFIED,
                    details=success_msg
                )
                return VerificationStatus.VERIFIED, username, success_msg

            finally:
                await context.close()

    async def interactive_login(self, timeout_seconds: int = 300) -> Tuple[bool, Optional[str], str]:
        """
        Opens a visible browser for manual login and waits until login is complete.
        Allows manual completion of CAPTCHA/MFA.
        """
        async with async_playwright() as p:
            context: BrowserContext = await p.chromium.launch_persistent_context(
                user_data_dir=self.profile_dir,
                headless=False,
                viewport={"width": 1280, "height": 900},
                args=["--disable-blink-features=AutomationControlled"]
            )
            try:
                page = await context.new_page()
                logger.info("Opening LeetCode login page in visible browser...")
                await page.goto("https://leetcode.com/accounts/login/", wait_until="domcontentloaded", timeout=45000)

                print("\n" + "=" * 60)
                print("MANUAL LEETCODE LOGIN REQUIRED")
                print("1. Log in manually in the opened browser window.")
                print("2. Complete any CAPTCHA or Two-Factor Authentication (MFA).")
                print("3. Antigravity will detect your login automatically once completed.")
                print(f"Waiting up to {timeout_seconds} seconds...")
                print("=" * 60 + "\n")

                start = time.time()
                while time.time() - start < timeout_seconds:
                    is_signed_in, username = await self.get_active_username(page)
                    if is_signed_in and username:
                        logger.info(f"Detected login for username: {username}")
                        if self.expected_username and username.lower() != self.expected_username.lower():
                            msg = (
                                f"Warning: Authenticated username '{username}' does not match "
                                f"EXPECTED_LEETCODE_USERNAME '{self.expected_username}'."
                            )
                            DatabaseManager.record_account_verification(
                                username=username,
                                expected_username=self.expected_username,
                                status=VerificationStatus.MISMATCH,
                                details=msg
                            )
                            return False, username, msg

                        msg = f"Successfully authenticated as '{username}'!"
                        DatabaseManager.record_account_verification(
                            username=username,
                            expected_username=self.expected_username or username,
                            status=VerificationStatus.VERIFIED,
                            details=msg
                        )
                        return True, username, msg

                    await asyncio.sleep(2)

                return False, None, f"Login timed out after {timeout_seconds} seconds."

            finally:
                await context.close()
