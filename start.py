import os
import re
from getpass import getpass
from time import sleep

from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait


def open_time_overview_page(driver):
    try:
        workday_hamburger_menu = WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located((By.CSS_SELECTOR, '[data-uxi-element-id="global-nav-button"]')))
    except TimeoutException:
        raise ValueError("Loading the Workday page took too much time")

    sleep(2)
    workday_hamburger_menu.click()

    sleep(2)
    for item in driver.find_elements(By.CSS_SELECTOR, '[data-automation-id="globalNavAppItemLink"]'):
        if item.text == "Time":
            time_elem = item
            break

    time_elem.click()
    try:
        WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located((By.CSS_SELECTOR, '[title="Time Off Balance"]')))
    except TimeoutException:
        raise ValueError("Loading the Workday page took too much time")


def open_this_week_page(driver):
    open_time_overview_page(driver)
    sleep(2)
    for button in driver.find_elements(By.TAG_NAME, "button"):
        if "This Week" in button.accessible_name:
            button.click()
            break


def rh_sso_login(driver, login, psw):
    try:
        username_elem = WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located((By.ID, "username")))
        psw_elem = WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located((By.ID, "password")))
    except TimeoutException:
        raise ValueError("Loading the RH SSO Login page took too much time")

    username_elem.clear()
    username_elem.send_keys(login)

    psw_elem.clear()
    psw_elem.send_keys(psw)

    submit_button = driver.find_element(By.ID, "submit")
    submit_button.click()


def get_quick_add_button(driver):
    try:
        actions_button = WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located((By.CSS_SELECTOR, '[title="Actions"]')))
        actions_button.click()
    except TimeoutException:
        raise ValueError("Loading the Workday page took too much time")
    
    try:
        return driver.find_element(By.CSS_SELECTOR, '[data-automation-label="Quick Add"]')
    except NoSuchElementException:
        return None


def click_next_week_button(driver):
    next_week_button = driver.find_element(By.CSS_SELECTOR, '[data-automation-id="nextMonthButton"]')
    next_week_button.click()
    sleep(2)


def click_previous_week_button(driver):
    previous_week_button = driver.find_element(By.CSS_SELECTOR, '[data-automation-id="prevMonthButton"]')
    previous_week_button.click()
    sleep(2)


def find_first_week(driver):
    """
    Find first week where is accessible "Quick Add" option under "Actions".
    """
    while True:
        if not get_quick_add_button(driver):
            click_next_week_button(driver)
            break
        click_previous_week_button(driver)


def get_pre_filled_hours(driver):
    pre_filled_hours = {
        "Mon": {"index": 0, "hours": None}, 
        "Tue": {"index": 1, "hours": None}, 
        "Wed": {"index": 2, "hours": None}, 
        "Thu": {"index": 3, "hours": None}, 
        "Fri": {"index": 4, "hours": None}, 
    }

    for index in range(5):
        css_selector = f'[data-automation-id="hoursEntered_{index}"]'
        working_hours_label = driver.find_element(By.CSS_SELECTOR, css_selector)
        for k, v in pre_filled_hours.items():
            if v["index"] == index:
                pre_filled_hours[k]["hours"] = int(working_hours_label.text.split()[1])
                break

    return pre_filled_hours


def select_days(driver, pre_filled_hours):
    day_added = False
    day_ids = {
        "Mon": "56$525708", 
        "Tue": "56$525705",
        "Wed": "56$525706",
        "Thu": "56$525703",
        "Fri": "56$525709",
    }
    for day, id in day_ids.items():
        if pre_filled_hours[day]["hours"] != 0:
            continue
        day_label = driver.find_element(By.CSS_SELECTOR, f'[data-uxi-form-item-label-id="{id}"]').get_property("id")
        checkbox_id = day_label.strip("-formLabel")
        day_checkbox = driver.find_element(By.CSS_SELECTOR, f'[id="{checkbox_id}"]')
        if day_checkbox.get_attribute("data-automationcheckboxenabled") == "true":
            day_checkbox.click()
            day_added = True
    sleep(3)
    return day_added


def click_next_button(driver):
    sleep(1)
    driver.execute_script("window.scrollBy(0, 500)")
    try:
        next_button = WebDriverWait(driver, 10).until(expected_conditions.presence_of_element_located((By.CSS_SELECTOR, '[data-automation-id="wd-CommandButton"]')))
    except TimeoutException:
        raise ValueError("Loading the Workday page took too much time")
    sleep(1)
    next_button.click()
    sleep(2)


def select_out_reason(driver, option):
    out_reason_elem = driver.find_element(By.CSS_SELECTOR, '[data-automation-id="selectWidget"]')
    out_reason_elem.click()
    sleep(1)
    meal_option_elem = driver.find_element(By.CSS_SELECTOR, f'[data-automation-label="{option}"]')
    meal_option_elem.click()
    sleep(1)


def click_add_button(driver):
    add_button = driver.find_element(By.CSS_SELECTOR, '[data-automation-id="panelSetAddButton"]')
    add_button.click()
    sleep(2)


def get_in_and_out_elements(driver):
    labels = driver.find_elements(By.TAG_NAME, "label")
    for l in labels:
        if l.text == "In":
            in_label_id = l.get_attribute("data-uxi-form-item-label-id")
        if l.text == "Out":
            out_label_id = l.get_attribute("data-uxi-form-item-label-id")
    
    inputs = driver.find_elements(By.TAG_NAME, "input")
    for i in inputs:
        if i.get_attribute("aria-labelledby") and in_label_id in i.get_attribute("aria-labelledby"):
            in_elem = i
        if i.get_attribute("aria-labelledby") and out_label_id in i.get_attribute("aria-labelledby"):
            out_elem = i
    return in_elem, out_elem


def fill_in_working_hours(driver):
    template = os.environ.get("TEMPLATE")
    pattern = r"^(?P<in1>([1-9]|[01][0-9]|2[0-3]):([0-5][0-9]))-(?P<out1>([1-9]|[01][0-9]|2[0-3]):([0-5][0-9]))($|(\+)(?P<in2>([1-9]|[01][0-9]|2[0-3]):([0-5][0-9]))-(?P<out2>([1-9]|[01][0-9]|2[0-3]):([0-5][0-9]))$)"
    match = re.match(pattern, template)
    if not match:
        raise ValueError("Invalid TEMPLATE for working hours.")
    
    in1 = match.group("in1")
    out1 = match.group("out1")
    in2 = match.group("in2")
    out2 = match.group("out2")
    
    in_elem, out_elem = get_in_and_out_elements(driver)
    in_elem.send_keys(in1)
    out_elem.send_keys(out1)
    sleep(2)

    if not in2:
        return

    select_out_reason(driver, "Meal")
    click_add_button(driver)

    in_elem, out_elem = get_in_and_out_elements(driver)
    in_elem.send_keys(in2)
    out_elem.send_keys(out2)
    sleep(2)


def click_ok_button(driver):
    driver.execute_script("window.scrollBy(0, 500)")
    ok_button = driver.find_element(By.CSS_SELECTOR, '[data-automation-id="wd-CommandButton"]')
    ok_button.click()
    sleep(3)


def click_back_button(driver):
    driver.execute_script("window.scrollBy(0, 500)")
    back_button = driver.find_element(By.CSS_SELECTOR, '[title="Back"]')
    back_button.click()
    sleep(1)


def click_cancel_button(driver):
    driver.execute_script("window.scrollBy(0, 500)")
    cancel_button = driver.find_element(By.CSS_SELECTOR, '[data-automation-id="wd-CommandButton_uic_cancelButton"]')
    cancel_button.click()
    sleep(3)


def main():
    load_dotenv()
    print("Starting 'End of the month' task ...")
    print(f"Using template {os.getenv('TEMPLATE')}")
    print(f"Login with {os.getenv('LOGIN')}")
    print("(TEMPLATE and LOGIN can be set in the .env file)")

    login = os.environ.get("LOGIN")
    psw = getpass("PASSWORD: ")

    driver = webdriver.Chrome()
    driver.get("https://wd5.myworkday.com/redhat")

    rh_sso_login(driver, login, psw)

    open_this_week_page(driver)

    find_first_week(driver)

    while True:
        data_range_title_elem = driver.find_element(By.CSS_SELECTOR, '[data-automation-id="dateRangeTitle"]')
        quick_add_button = get_quick_add_button(driver)
        sleep(1)

        if not quick_add_button:
            break

        print(f"Processing week {data_range_title_elem.text}")
        pre_filled_hours = get_pre_filled_hours(driver)
        quick_add_button.click()
        click_next_button(driver)
        days_selected = select_days(driver, pre_filled_hours)

        if days_selected:
            fill_in_working_hours(driver)
            click_ok_button(driver)
        else:
            click_back_button(driver)
            click_cancel_button(driver)

        click_next_week_button(driver)

    sleep(2)
    driver.quit()
    print("... end of 'End of the month' task")


if __name__ == "__main__":
    main()
