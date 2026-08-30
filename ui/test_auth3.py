import asyncio
import json
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        console_msgs = []
        page.on('console', lambda msg: console_msgs.append(f'[{msg.type}] {msg.text}'))
        page.on('pageerror', lambda err: console_msgs.append(f'[PAGE ERROR] {err}'))
        
        responses = []
        page.on('response', lambda r: responses.append(r))
        
        # Test registration with VALID password (no sequential chars)
        print('=== REGISTER TEST with valid password ===')
        await page.goto('http://localhost:3000/register', wait_until='networkidle', timeout=15000)
        await page.wait_for_timeout(2000)
        
        await page.fill('input[id="firstName"]', 'Test')
        await page.fill('input[id="lastName"]', 'User')
        await page.fill('input[id="regEmail"]', 'test3@example.com')
        await page.fill('input[id="password"]', 'MyStr0ng#Pass')
        
        # Fill confirm password
        confirm_inputs = await page.query_selector_all('input[id="confirmPassword"]')
        if confirm_inputs:
            await confirm_inputs[0].fill('MyStr0ng#Pass')
        
        # Check terms
        terms = await page.query_selector('input[type="checkbox"]')
        if terms and not await terms.is_checked():
            await terms.check()
        
        await page.click('button:has-text("Create Account")')
        await page.wait_for_timeout(8000)
        
        print(f'URL after submit: {page.url}')
        content = await page.content()
        
        # Check for error messages
        error_el = await page.query_selector_all('[class*="error"], [class*="red"], [role="alert"]')
        for el in error_el:
            text = await el.inner_text()
            if text.strip() and len(text.strip()) > 5:
                print(f'Error: {text.strip()[:200]}')
        
        toast_el = await page.query_selector('[class*="toast"], [class*="Toast"]')
        if toast_el:
            toast_text = await toast_el.inner_text()
            if toast_text.strip():
                print(f'Toast: {toast_text.strip()[:300]}')
        
        print()
        print('=== AUTH NETWORK RESPONSES ===')
        for r in responses:
            if '/auth/' in r.url:
                print(f'  {r.status} {r.url}')
                try:
                    body = await r.text()
                    print(f'    Body: {body[:500]}')
                except:
                    print(f'    (could not read body)')
        
        print()
        print('=== CONSOLE MESSAGES ===')
        for msg in console_msgs:
            print(f'  {msg}')
        
        # Check if login was successful by checking localStorage
        tokens = await page.evaluate('''() => {
            return {
                access_token: localStorage.getItem('access_token'),
                refresh_token: localStorage.getItem('refresh_token'),
                user: localStorage.getItem('user'),
            };
        }''')
        print()
        print('=== LOCALSTORAGE ===')
        print(f'  access_token: {tokens["access_token"][:50] if tokens["access_token"] else "None"}...')
        print(f'  refresh_token: {tokens["refresh_token"][:50] if tokens["refresh_token"] else "None"}...')
        print(f'  user: {tokens["user"][:100] if tokens["user"] else "None"}')
        
        await browser.close()

asyncio.run(test())
