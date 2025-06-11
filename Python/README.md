## auto_add_counties.py — Quick‑Start

Automate county taxonomy setup on a local Drupal site using Selenium.

## Prereqs

    Python 3.x

    Google Chrome

    ChromeDriver in system PATH

    Selenium

    pip install selenium

## What It Does

- Opens Chrome and goes to the local Drupal login page.

- Logs in using your credentials (add these in the script).

- Visits the county taxonomy add page for each Oregon county.

- Adds all 36 counties one by one.

- Waits briefly between actions to allow page loads.

## Setup

    Edit the script:

        Add your Drupal username and password in the auto_login() function.

    Make sure Drupal is running at:

http://drupal-website:8888

Run the script:

    python auto_add_counties.py

Notes

    Script uses hardcoded XPaths. Update them if your Drupal UI differs.

    Intended for local/test environments only — not production-safe.

    This script can be modified to add any python list of any size to a Drupal taxonomy