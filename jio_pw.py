from playwright.sync_api import sync_playwright
import json
import time

def intercept_api():
    with sync_playwright() as p:
        # Launch browser 
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            viewport={'width': 1280, 'height': 720}
        )
        page = context.new_page()

        api_data = None

        def handle_response(response):
            nonlocal api_data
            if 'locatorapi.php' in response.url and response.status == 200:
                print(f"Intercepted API Response from {response.url}")
                try:
                    text = response.text()
                    try:
                        api_data = json.loads(text)
                    except json.JSONDecodeError:
                        print("Failed to decode JSON, writing raw text.")
                        api_data = text
                except Exception as e:
                    print(f"Error reading response body: {e}")

        page.on("response", handle_response)
        
        print("Navigating to Jio-bp locator...")
        try:
            page.goto("https://www.jiobp.com/locate-fuel-station", timeout=60000, wait_until="networkidle")
        except Exception as e:
            print(f"Navigation error (might just be a timeout): {e}")

        # Wait a bit just to ensure the XHR completes
        page.wait_for_timeout(5000)

        # Let's also check if data was stored in JS vars `res` or `data3` within the page!
        if not api_data:
            print("No network interception caught it, attempting to extract 'data3' JS variable from page.")
            try:
                data3 = page.evaluate("data3")
                if data3:
                    api_data = data3
            except Exception as e:
                print("JS Evaluation error:", e)

        if api_data:
            print(f"Successfully captured data! Saving to jiobp_raw.json")
            with open("jiobp_raw.json", "w", encoding="utf-8") as f:
                json.dump(api_data, f, ensure_ascii=False, indent=2)
            print("Done!")
        else:
            print("Failed to intercept or find data.")

        browser.close()

if __name__ == "__main__":
    intercept_api()
