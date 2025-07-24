from playwright.async_api import async_playwright
from Decrypt import EncryptionSystem
from order import get_order
import asyncio
import base64
import re

version = "2da0f651ee9ae6514d94367ef7e16e266a9671c34e27d2e95f970da6fa504071"

async def capture_hcaptcha_requests():

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()
        click_payload = None

        async def handle_request(request):
            nonlocal click_payload
            if any(domain in request.url for domain in ['hcaptcha.com', 'hcaptcha.net']):
                if request.method == 'POST':
                    try:
                        click_payload = request.post_data
                    except UnicodeDecodeError:
                        try:
                            post_data_bytes = request.post_data_buffer
                            if post_data_bytes:
                                click_payload = base64.b64encode(post_data_bytes).decode('ascii')
                            else:
                                raise Exception("Data is invalid")
                        except Exception as e:
                            raise Exception(e)

        page.on('request', handle_request)
        
        try:
            print("Navigating to hCaptcha demo...")

            await page.goto('https://accounts.hcaptcha.com/demo')
            
            await page.wait_for_timeout(3000)

            iframe_element = await page.wait_for_selector('iframe[src*="hcaptcha.com"]', timeout=10000)

            iframe = await iframe_element.content_frame()
            
            if iframe:
                checkbox = await iframe.wait_for_selector('[role="checkbox"]', timeout=10000)
                click_payload = None
                await checkbox.click()
                print("Clicked on hCaptcha checkbox")
                await page.wait_for_timeout(2000)
            else:
                raise Exception("Failed to locate iframe")
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            await browser.close()

            return click_payload

def extract_order(decrypted_main_data, system, remove_messages=True):

    def get_substring(body: str, begin: str, end: str) -> str:
        start_index = body.find(begin)
        if start_index == -1:
            return "-1"
        
        start_index += len(begin)
        end_index = body.find(end, start_index)
        
        if end_index == -1:
            return "-1"
        
        return body[start_index:end_index]

    def extract_blob(n_data):
        quoted_strings = re.findall(r'"(.*?)"', n_data)

        blob = max(quoted_strings, key=len)

        n_data = n_data.replace(blob, "<blob>")

        return n_data, blob

    n_data = get_substring(decrypted_main_data, "'n': '", "',")

    if n_data == "-1":
        print("\n\n\nN data is -1")
        return None
    
    try:
        decrypted_n_data = str(system.decrypt_n(n_data))
    except Exception as e:
        print("Decryption n failed:", str(e))

    if remove_messages:
        messages = get_substring(decrypted_n_data, '[["https:', "]]]")

        if messages != "-1":
            messages = '[["https:' + messages + "]]]"

            decrypted_n_data = decrypted_n_data.replace(messages, '"messages"')
        else:
            print("Failed to remove messages")

    decrypted_n_data, _ = extract_blob(decrypted_n_data)

    return get_order(decrypted_n_data)

def save_data(version: str):
    postData = asyncio.run(capture_hcaptcha_requests())

    if not postData:
        print("Failed to get post data")
        return
    
    order = {}
    shouldSave = False
    system = EncryptionSystem(version, order, shouldSave)
    
    try:
        decrypted_main_data = str(system.decrypt_request_payload(base64.b64decode(postData)))
    except Exception as e:
        print("Decryption request failed:", str(e))
        return
    
    order = extract_order(decrypted_main_data, system)

    system.save_system(order)

if __name__ == "__main__":
    save_data(version)
