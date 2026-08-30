from playwright.sync_api import sync_playwright

# Test 1: Login
print("=" * 60)
print("TEST 1: LOGIN")
print("=" * 60)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context()
    
    console_messages = []
    page_events = []
    
    context.on("console", lambda msg: console_messages.append(f"{msg.type}: {msg.text}"))
    
    page = context.new_page()
    
    # Network request tracking
    request_urls = []
    response_urls = []
    page.on("request", lambda req: request_urls.append(req.url))
    page.on("response", lambda resp: response_urls.append((resp.url, str(resp.status))))
    
    # Navigate to login
    print("Navigating to /login...")
    page.goto("http://localhost:3001/login", wait_until="networkidle")
    page.wait_for_timeout(2000)
    page.screenshot(path="login_before.png")
    
    # Check what inputs are available
    inputs = page.query_selector_all("input")
    print(f"Found {len(inputs)} input elements on login page")
    
    for i, el in enumerate(inputs):
        tag = el.evaluate("el => el.tagName")
        inp_type = el.evaluate("el => el.type")
        inp_id = el.evaluate("el => el.id")
        inp_name = el.evaluate("el => el.name")
        inp_placeholder = el.evaluate("el => el.placeholder")
        print(f"  Input {i}: tag={tag}, type={inp_type}, id={inp_id}, name={inp_name}, placeholder={inp_placeholder}")
    
    # Fill credentials using id selectors
    page.fill('input[id="email"]', 'admin@marketplace.local')
    page.fill('input[id="password"]', 'Adm1n@2026!')
    page.screenshot(path="login_filled.png")
    
    # Submit
    page.click('button[type="submit"]')
    page.wait_for_timeout(5000)
    page.screenshot(path="login_after.png")
    
    current_url = page.url
    content = page.content()
    
    print(f"\nURL after login: {current_url}")
    print(f"Content length: {len(content)}")
    
    # Check for error messages
    error_el = page.query_selector('.text-red-500, .text-red-700, [class*="red"], .toast-error, [class*="error"]')
    if error_el:
        print(f"Error message found: {error_el.inner_text().strip()}")
    
    print(f"\nRequest URLs ({len(request_urls)}):")
    for url in request_urls:
        print(f"  -> {url}")
    
    print(f"\nResponse URLs ({len(response_urls)}):")
    for url, status in response_urls:
        print(f"  <- {url} [{status}]")
    
    print(f"\nConsole messages ({len(console_messages)}):")
    for msg in console_messages:
        try:
            print(f"  {msg}")
        except Exception:
            print(f"  {msg.encode('ascii', 'replace').decode()}")
    
    # Check if error indicators present
    if any(kw in content.lower() for kw in ['network error', 'cannot', 'failed to fetch', 'net::', 'ERR_', 'timeout']):
        print("\n*** NETWORK ERROR DETECTED ***")
    
    browser.close()

# Test 2: Registration
print()
print("=" * 60)
print("TEST 2: REGISTRATION")
print("=" * 60)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    request_urls = []
    response_urls = []
    page.on("request", lambda req: request_urls.append(req.url))
    page.on("response", lambda resp: response_urls.append((resp.url, str(resp.status))))
    
    # Navigate to register
    print("Navigating to /register...")
    page.goto("http://localhost:3001/register", wait_until="networkidle")
    page.wait_for_timeout(2000)
    page.screenshot(path="register_before.png")
    
    # Check inputs
    inputs = page.query_selector_all("input")
    print(f"Found {len(inputs)} input elements on register page")
    
    for i, el in enumerate(inputs):
        tag = el.evaluate("el => el.tagName")
        inp_type = el.evaluate("el => el.type")
        inp_id = el.evaluate("el => el.id")
        inp_name = el.evaluate("el => el.name")
        inp_placeholder = el.evaluate("el => el.placeholder")
        print(f"  Input {i}: tag={tag}, type={inp_type}, id={inp_id}, name={inp_name}, placeholder={inp_placeholder}")
    
    # Fill registration form using id selectors
    page.fill('input[id="firstName"]', 'Test')
    page.fill('input[id="lastName"]', 'User')
    page.fill('input[id="regEmail"]', 'testuser@example.com')
    page.fill('input[id="password"]', 'MyStr0ng#Pass!')
    page.fill('input[id="confirmPassword"]', 'MyStr0ng#Pass!')
    page.screenshot(path="register_filled.png")
    
    # Check terms checkbox
    terms_checked = page.is_checked('input[type="checkbox"]')
    print(f"Terms checkbox initially checked: {terms_checked}")
    if not terms_checked:
        page.check('input[type="checkbox"]')
    
    # Submit
    page.click('button[type="submit"]')
    page.wait_for_timeout(5000)
    page.screenshot(path="register_after.png")
    
    current_url = page.url
    content = page.content()
    
    print(f"\nURL after register: {current_url}")
    print(f"Content length: {len(content)}")
    
    # Check for error messages
    error_el = page.query_selector('.text-red-500, .text-red-700, [class*="red"], .toast-error, [class*="error"]')
    if error_el:
        print(f"Error message found: {error_el.inner_text().strip()}")
    
    print(f"\nRequest URLs ({len(request_urls)}):")
    for url in request_urls:
        print(f"  -> {url}")
    
    print(f"\nResponse URLs ({len(response_urls)}):")
    for url, status in response_urls:
        print(f"  <- {url} [{status}]")
    
    browser.close()
