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
        
        # Test login
        print('=== LOGIN TEST ===')
        await page.goto('http://localhost:3000/login', wait_until='networkidle', timeout=15000)
        await page.wait_for_timeout(2000)
        
        await page.fill('input[type="email"]', 'admin@marketplace.local')
        await page.fill('input[type="password"]', 'Adm1n@2026!')
        
        await page.click('button[type="submit"]')
        await page.wait_for_timeout(8000)
        
        print(f'URL after submit: {page.url}')
        content = await page.content()
        
        # Check for error messages in DOM
        error_texts = []
        error_el = await page.query_selector_all('[class*="error"], [class*="red"], [role="alert"]')
        for el in error_el:
            text = await el.inner_text()
            if text.strip() and len(text.strip()) > 5:
                error_texts.append(text.strip()[:200])
        
        if error_texts:
            print('Error elements found:')
            for t in error_texts[:5]:
                print(f'  - {t}')
        
        # Check toast
        toast_el = await page.query_selector('[class*="toast"], [class*="Toast"]')
        if toast_el:
            toast_text = await toast_el.inner_text()
            if toast_text.strip():
                print(f'Toast content: {toast_text.strip()[:300]}')
        
        # Print console messages
        print()
        print('=== CONSOLE MESSAGES ===')
        for msg in console_msgs:
            print(f'  {msg}')
        
        # Print auth-related network responses
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
        
        # Check API accessibility
        print()
        print('=== API GATEWAY CHECK ===')
        resp8089 = await page.evaluate('''async () => {
            try {
                const res = await fetch("http://localhost:8089/auth/login", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({email: "test@test.com", password: "test"})
                });
                return {status: res.status, statusText: res.statusText, body: await res.text()};
            } catch(e) {
                return {error: e.message};
            }
        }''')
        print(f'  Port 8089: {json.dumps(resp8089)}')
        
        resp8080 = await page.evaluate('''async () => {
            try {
                const res = await fetch("http://localhost:8080/auth/login", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({email: "test@test.com", password: "test"})
                });
                return {status: res.status, statusText: res.statusText, body: await res.text()};
            } catch(e) {
                return {error: e.message};
            }
        }''')
        print(f'  Port 8080: {json.dumps(resp8080)}')
        
        # Test register
        print()
        print('=== REGISTER TEST ===')
        console_msgs.clear()
        responses.clear()
        
        await page.goto('http://localhost:3000/register', wait_until='networkidle', timeout=15000)
        await page.wait_for_timeout(2000)
        
        await page.fill('input[id="firstName"]', 'Test')
        await page.fill('input[id="lastName"]', 'User')
        await page.fill('input[id="regEmail"]', 'test2@example.com')
        await page.fill('input[id="password"]', 'Test1234!')
        
        # Fill confirm password (second password input)
        password_inputs = await page.query_selector_all('input[id="confirmPassword"]')
        if password_inputs:
            await password_inputs[0].fill('Test1234!')
        
        # Check terms
        terms = await page.query_selector('input[type="checkbox"]')
        if terms and not await terms.is_checked():
            await terms.check()
        
        await page.click('button:has-text("Create Account")')
        await page.wait_for_timeout(8000)
        
        print(f'URL after submit: {page.url}')
        content = await page.content()
        
        error_texts = []
        error_el = await page.query_selector_all('[class*="error"], [class*="red"], [role="alert"]')
        for el in error_el:
            text = await el.inner_text()
            if text.strip() and len(text.strip()) > 5:
                error_texts.append(text.strip()[:200])
        
        if error_texts:
            print('Error elements found:')
            for t in error_texts[:5]:
                print(f'  - {t}')
        
        toast_el = await page.query_selector('[class*="toast"], [class*="Toast"]')
        if toast_el:
            toast_text = await toast_el.inner_text()
            if toast_text.strip():
                print(f'Toast content: {toast_text.strip()[:300]}')
        
        print()
        print('=== CONSOLE MESSAGES ===')
        for msg in console_msgs:
            print(f'  {msg}')
        
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
        
        await browser.close()

asyncio.run(test())
