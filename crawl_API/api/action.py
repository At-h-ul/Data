from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def goBack(driver):
        back_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@value='Back']"))
        )
        back_button.click()

def destroyDatatable(driver):

        js_string = "$('#example').DataTable().destroy();"
        driver.execute_script(js_string)
        time.sleep(3)  # Allow table to reload