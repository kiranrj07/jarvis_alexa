import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, WebDriverException

# Load environment variables from .env file
load_dotenv()
AMAZON_USERNAME = os.getenv("AMAZON_USERNAME")
AMAZON_PASSWORD = os.getenv("AMAZON_PASSWORD")

# --- Configure Chrome Driver Options ---
options = Options()
options.add_argument("--window-size=1920,1080")
options.add_argument("--start-maximized")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--force-device-scale-factor=0.75") 
# options.add_argument("--headless") 

# driver is initialized inside update_alexa_endpoint now
# and managed within its try...finally block.

# --- Reusable Wait Function ---
def wait_for_element(by, value, timeout=30, action=None, keys=None):
    # 'driver' needs to be accessible here, so we assume it's initialized by the calling function.
    # In update_alexa_endpoint, it's now initialized.
    try:
        if action == "click":
            element = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            element.click()
        elif action == "send_keys" and keys is not None:
            element = WebDriverWait(driver, timeout).until(
                EC.visibility_of_element_located((by, value))
            )
            element.clear()
            element.send_keys(keys)
        else:
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
        return element
    except TimeoutException:
        raise Exception(f"[ERROR] Element not found or not interactable within {timeout} seconds: {value}")
    except Exception as e:
        raise Exception(f"[ERROR] An unexpected error occurred while waiting for element '{value}': {e}")

# --- Function to Handle the Modal Popup (Enhanced) ---
def close_build_skills_modal_if_present():
    print("[DEBUG] Attempting to close 'Build skills faster with the global build update' modal popup if present...")
    
    modal_dialog_xpath = "//span[contains(@class, 'astro-modal-dialog') and contains(@class, 'getting-started-modal')]"
    close_button_xpath = "/html/body/div[5]/span/div/div[2]/div/div[2]/button[1]/span"

    try:
        print("[DEBUG] Strategy 1: Waiting for modal dialog to become visible...")
        WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.XPATH, modal_dialog_xpath)))
        print("[DEBUG] Modal dialog is visible. Trying to close...")

        print("[DEBUG] Strategy 2: Attempting to close modal with ESCAPE key...")
        driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
        
        WebDriverWait(driver, 7).until(EC.invisibility_of_element_located((By.XPATH, modal_dialog_xpath)))
        print("[DEBUG] Modal popup successfully closed with ESCAPE key.")
        time.sleep(1)
        return True

    except TimeoutException:
        print("[DEBUG] Modal dialog did not become visible within 5 seconds. It's likely not present.")
        return False

    except Exception as e_escape:
        print(f"[WARNING] ESCAPE key did not close the modal or encountered an error: {e_escape}. Trying click strategy...")
        try:
            print("[DEBUG] Strategy 3: Attempting to click the 'Close' button directly...")
            close_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, close_button_xpath))
            )
            close_button.click()
            print("[DEBUG] 'Build skills faster' modal popup close button clicked.")
            
            WebDriverWait(driver, 7).until(EC.invisibility_of_element_located((By.XPATH, modal_dialog_xpath)))
            print("[DEBUG] Modal popup successfully closed by clicking button.")
            time.sleep(1)
            return True

        except ElementClickInterceptedException as e_click_intercepted:
            print(f"[WARNING] Close button click intercepted for modal: {e_click_intercepted}. Trying JavaScript click as fallback.")
            try:
                element_to_click = driver.find_element(By.XPATH, close_button_xpath)
                driver.execute_script("arguments[0].click();", element_to_click)
                print("[DEBUG] Close button clicked via JavaScript.")
                WebDriverWait(driver, 7).until(EC.invisibility_of_element_located((By.XPATH, modal_dialog_xpath)))
                print("[DEBUG] Modal popup successfully closed via JavaScript click.")
                time.sleep(1)
                return True
            except Exception as js_e:
                print(f"[ERROR] Failed to close modal even with JavaScript click: {js_e}")
                return False
        except Exception as e_click:
            print(f"[ERROR] Failed to close modal by clicking button: {e_click}")
            return False

    return False


# --- Main Automation Function ---
def update_alexa_endpoint(ngrok_url):
    global driver # Declare driver as global to ensure wait_for_element can access it.
                  # It's initialized here.
    
    try:
        driver = webdriver.Chrome(service=ChromeService(), options=options) # Initialize driver here

        print("[DEBUG] Opening Alexa Developer Console...")
        driver.get("https://developer.amazon.com/alexa/console/ask")

        # --- Login Process ---
        print("[DEBUG] Logging into Amazon...")
        wait_for_element(By.ID, "ap_email", action="send_keys", keys=AMAZON_USERNAME)
        wait_for_element(By.ID, "continue", action="click")
        wait_for_element(By.ID, "ap_password", action="send_keys", keys=AMAZON_PASSWORD)
        wait_for_element(By.ID, "signInSubmit", action="click")

        # --- Select the Skill ---
        print("[DEBUG] Waiting for Gemini Assistant skill to load and selecting it...")
        gemini_skill_link_xpath = '//*[@id="tenant-content"]/div/div/div/div/div[4]/div[1]/div[1]/div[2]/div/div/div[2]/table/tbody/tr/td[2]/span/span/a/span'
        wait_for_element(By.XPATH, gemini_skill_link_xpath, action="click")

        time.sleep(5) 

        print("[DEBUG] Waiting for 15 seconds before the first attempt to close modal popup...")
        time.sleep(15) 

        close_build_skills_modal_if_present()

        # --- Navigate to Endpoint Tab with Robust Retry Logic ---
        print("[DEBUG] Navigating to Endpoint tab...")
        endpoint_tab_xpath = '//*[@id="root"]/div/div[1]/nav/ol/li[8]/span/span/a'

        max_retries = 5
        retry_delay = 3
        endpoint_clicked = False

        for i in range(max_retries):
            try:
                modal_dialog_xpath = "//span[contains(@class, 'astro-modal-dialog') and contains(@class, 'getting-started-modal')]"
                print(f"[DEBUG] Before clicking Endpoint tab (Retry {i+1}/{max_retries}): Ensuring modal is invisible...")
                try:
                    WebDriverWait(driver, 5).until(EC.invisibility_of_element_located((By.XPATH, modal_dialog_xpath)))
                    print("[DEBUG] Modal confirmed invisible.")
                except TimeoutException:
                    print("[WARNING] Modal still visible or reappeared! Attempting to close it again before clicking Endpoint.")
                    if close_build_skills_modal_if_present():
                        WebDriverWait(driver, 5).until(EC.invisibility_of_element_located((By.XPATH, modal_dialog_xpath)))
                        print("[DEBUG] Modal (re)closed and confirmed invisible.")
                    else:
                        print("[ERROR] Modal could not be closed even after re-attempt. This might cause further interception.")

                wait_for_element(By.XPATH, endpoint_tab_xpath, action="click", timeout=10)
                print("[DEBUG] Successfully navigated to Endpoint tab.")
                endpoint_clicked = True
                break
            except ElementClickInterceptedException:
                print(f"[WARNING] Element click intercepted when navigating to Endpoint tab (Retry {i+1}/{max_retries}). Attempting to close modal again...")
                close_build_skills_modal_if_present()
                time.sleep(retry_delay)
            except Exception as e:
                print(f"[WARNING] An error occurred navigating to Endpoint tab (Retry {i+1}/{max_retries}): {e}. Retrying...")
                time.sleep(retry_delay)
        
        if not endpoint_clicked:
            print("[WARNING] All standard attempts failed to click Endpoint tab. Trying JavaScript click as fallback.")
            try:
                endpoint_element = driver.find_element(By.XPATH, endpoint_tab_xpath)
                driver.execute_script("arguments[0].click();", endpoint_element)
                print("[DEBUG] Endpoint tab clicked via JavaScript fallback.")
            except Exception as js_e:
                raise Exception(f"[CRITICAL ERROR] Failed to navigate to Endpoint tab after {max_retries} attempts and JavaScript fallback: {js_e}")

        # --- Update Default Region Endpoint ---
        print("[DEBUG] Updating Default Region endpoint...")
        default_region_input_xpath = '//*[@id="root"]/div/div[2]/div[2]/div[2]/div[4]/div[2]/div/div[1]/div/div[2]/form[1]/div[1]/div[1]/input'
        
        endpoint_input = wait_for_element(By.XPATH, default_region_input_xpath)
        
        endpoint_input.send_keys(Keys.CONTROL + "a")
        endpoint_input.send_keys(Keys.DELETE)
        endpoint_input.send_keys(ngrok_url)

        # --- Save Changes ---
        print("[DEBUG] Saving changes...")
        save_button_xpath = '//*[@id="root"]/div/div[2]/header/section/div[2]/button/span'
        wait_for_element(By.XPATH, save_button_xpath, action="click")
        
        time.sleep(2)

        print("[SUCCESS] Alexa endpoint updated successfully!")

    except Exception as e:
        print(f"\n[CRITICAL ERROR] Automation failed: {e}")
        raise # Re-raise the exception so app.py can catch it

    finally:
        # This ensures the browser closes regardless of whether the try block succeeded or failed.
        if driver:
            print("[DEBUG] Quitting WebDriver.")
            driver.quit()


# --- Script Entry Point (for standalone testing of update_alexa_endpoint.py) ---
if __name__ == "__main__":
    print("Running update_alexa_endpoint.py in standalone mode.")
    test_ngrok_url = os.getenv("NGROK_PUBLIC_URL", "https://your-test-ngrok-url.ngrok-free.app/alexa") 
    try:
        update_alexa_endpoint(test_ngrok_url)
    except Exception as e:
        print(f"\n[CRITICAL ERROR] Standalone script execution failed: {e}")
