import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import pytest

# Assumes the app is running at http://localhost:8080
APP_URL = "http://localhost:8080"

@pytest.fixture(scope="module")
def driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()

def test_flight_planner_route_and_weather(driver):
    driver.get(APP_URL)
    # Wait for page to load
    time.sleep(2)
    # Fill out flight planner form
    from_input = driver.find_element(By.ID, "from-airport")
    to_input = driver.find_element(By.ID, "to-airport")
    range_input = driver.find_element(By.ID, "aircraft-range")
    gs_input = driver.find_element(By.ID, "groundspeed")
    submit_btn = driver.find_element(By.CSS_SELECTOR, "#flight-plan-form button[type='submit']")

    from_input.clear()
    from_input.send_keys("KPAO")
    to_input.clear()
    to_input.send_keys("7S5")
    range_input.clear()
    range_input.send_keys("400")
    gs_input.clear()
    gs_input.send_keys("120")
    submit_btn.click()

    # Wait for route to be planned and weather to be fetched
    time.sleep(5)
    summary = driver.find_element(By.ID, "route-summary").text
    assert "KPAO" in summary and "7S5" in summary
    assert "Total Distance" in summary
    assert "Estimated Time" in summary
    assert "Legs" in summary
    # Check that weather is shown for at least one leg
    assert "Temp:" in summary or "Weather unavailable" in summary

    # Optionally, check that a polyline and markers are present on the map
    map_svgs = driver.find_elements(By.CSS_SELECTOR, "#map svg path")
    assert len(map_svgs) > 0
