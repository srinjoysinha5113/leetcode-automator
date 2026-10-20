import asyncio
import json
from playwright.async_api import async_playwright

async def inspect():
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            "data/browser_profile",
            headless=True,
            viewport={"width": 1440, "height": 900}
        )
        page = await ctx.new_page()
        await page.goto("https://leetcode.com/problems/contains-duplicate/", wait_until="domcontentloaded")
        try:
            await page.wait_for_selector('.monaco-editor', timeout=20000)
            print("Monaco editor detected!")
        except Exception as e:
            print(f"Wait for editor: {e}")
        await asyncio.sleep(2)


        # Get all text from all buttons
        buttons = await page.evaluate("""() => {
            const arr = [];
            for (const b of document.querySelectorAll('button, div[role="button"]')) {
                const text = b.innerText ? b.innerText.trim() : '';
                if (text && text.length < 50) {
                    arr.push({
                        tag: b.tagName,
                        text: text,
                        className: b.className,
                        id: b.id,
                        ariaLabel: b.getAttribute('aria-label') || ''
                    });
                }
            }
            return arr;
        }""")

        with open("buttons.json", "w", encoding="utf-8") as f:
            json.dump(buttons, f, indent=2)

        print(f"Dumped {len(buttons)} buttons.")
        await ctx.close()

if __name__ == "__main__":
    asyncio.run(inspect())
