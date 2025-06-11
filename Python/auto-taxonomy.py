# Imports---------------------------

import time
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Get to Login page and login ---------------------------------

def auto_login():
    global driver
    driver = Chrome()
    driver.get('http://drupal-website:8888/user/login') # Log in to local Drupal website

    # Maximize current window
    driver.maximize_window()

    time.sleep(1) #Give break before attempting log in

    user_name = driver.find_element(By.XPATH, '//*[@id="edit-name"]') # Enter username
    user_name.send_keys('')

    time.sleep(2)

    pass_word = driver.find_element(By.XPATH, '//*[@id="edit-pass"]') #enter password
    pass_word.send_keys('')

    submit_button = driver.find_element(By.XPATH, '//*[@id="edit-submit"]')
    submit_button.click()

    time.sleep(2)

def add_state():
    counties = ['Baker', 'Benton', 'Clackamas', 'Clatsop', 'Columbia', 'Coos', 'Crook', 'Curry', 'Deschutes', 'Douglas', 'Gilliam', 'Grant', 'Harney', 'Hood River', 'Jackson', 'Jefferson', 'Josephine', 'Klamath', 'Lake', 'Lane', 'Lincoln', 'Linn', 'Malheur', 'Marion', 'Morrow', 'Multnomah', 'Polk', 'Sherman', 'Tillamook', 'Umatilla', 'Union', 'Wallowa', 'Wasco', 'Washington', 'Wheeler', 'Yamhill']
    for county in counties:
        driver.get('http://drupal-website:8888/admin/structure/taxonomy/manage/counties/add') #Navigate to the Counties taxonomy page
        county_name = driver.find_element(By.XPATH, '//*[@id="edit-name-0-value"]')
        county_name.send_keys(county)
        print('\n {} added.'.format(county)) #Report total number of imports

        save_button = driver.find_element(By.XPATH, '//*[@id="edit-submit"]')
        save_button.click()

        time.sleep(2)

auto_login()
add_state()
