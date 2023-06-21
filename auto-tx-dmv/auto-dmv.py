#!/usr/bin/env python3

from selenium import webdriver
from selenium.common import exceptions
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support.wait import WebDriverWait
import click
import time
import tomllib


DATEFMT = "%m/%d/%Y"


def normalize_date(datestr):
    return time.strftime(DATEFMT, time.strptime(datestr, DATEFMT))



def parse_table(web_element):
    lines = web_element.text.splitlines()

    # remove the table header
    body = lines[2:]

    current = []
    table = []
    for el in body:
        if el == "double_arrow":
            table += [current]
            current = []
        else:
            current += [el]

    if current != []:
        table += [current]

    result = []
    for row in table:
        dist_date = row[2].split(" ")
        result += [
            {
                "office": row[0],
                "address": row[1],
                "distance": float(dist_date[0]),
                "date": time.strptime(dist_date[-1], DATEFMT),
                "datestr": dist_date[-1],
            }
        ]

    return result


class Driver:
    def __init__(self, gui=True, browser="firefox"):
        match browser:
            case "firefox":
                options = FirefoxOptions()
                options.page_load_strategy = "normal"
                if not gui:
                    options.add_argument("--headless")

                self.driver = webdriver.Firefox(options=options)
            case "chrome":
                options = ChromeOptions()
                options.page_load_strategy = "normal"
                if not gui:
                    options.add_argument("--headless")

                self.driver = webdriver.Chrome(options=options)
            case x:
                raise Exception(
                    f"{x} is not a supported browser.\n"
                    + " [firefox, chrome] are valid options."
                )

        self.driver.implicitly_wait(2)

    def load(self, url):
        print(f"Loading {url}")
        self.driver.get(url)

    def click(self, text):
        WebDriverWait(self.driver, timeout=10).until(
            lambda d: d.find_element(By.XPATH, f"//button[normalize-space()='{text}']")
        )
        for i in range(5):
            if i == 5:
                raise Exception("Failed")

            try:
                self.driver.find_element(
                    By.XPATH, f"//button[normalize-space()='{text}']"
                ).click()
                print(f"Clicked {text}")
                # if we successfully click, break the loop
                break
            except exceptions.ElementClickInterceptedException as e:
                print("Failed clicking, waiting to try again")
                print(e)
                time.sleep(2)
                pass

    def fill(self, label, text):
        field = self.driver.find_element(
            By.XPATH, f"//label[normalize-space()='{label}']/following::input[1]"
        )
        if isinstance(text, str):
            field.send_keys(text)
        elif isinstance(text, list):
            for t in text:
                field.send_keys(t)

    def css(self, text):
        return self.driver.find_elements(By.CSS_SELECTOR, text)

    def button_exists(self, text) -> bool:
        elems = self.driver.find_elements(
            By.XPATH, f"//button[normalize-space()='{text}']"
        )
        return elems != []

    def quit(self):
        self.driver.quit()


def make_appointment(
        driver,
        date,
        datestr,
        best_current
):
    # make the appointment!
    if best_current is None or date < best_current:
        print("Yahooo!!!!!")
        appts = driver.driver.find_elements(By.CSS_SELECTOR, ".card.blue")
        for card in appts:
            print(card.text)
            if datestr in card.text:
                card.click()
                break

        slots = driver.driver.find_elements(By.CSS_SELECTOR, ".slot-card.blue-grey")
        if len(slots) > 0:
            slots[0].click()

        els = driver.driver.find_elements(By.CSS_SELECTOR, ".button")
        for e in els:
            if "NEXT" in e.text:
                e.click()
                break
        driver.click("Confirm")
        best_current = date
    else:
        print("Didn't find anything sooner :(")

    print("Finished, waiting 30 secs")
    time.sleep(30)

    return best_current


def find_appointments(
    driver: Driver | None = None,
    firstname: str | None = None,
    lastname: str | None = None,
    dob: str | None = None,
    ssn: str | None = None,
    cell: str | None = None,
    email: str | None = None,
    zipcode: str | None = None,
):
    assert isinstance(driver, Driver)
    assert isinstance(firstname, str)
    assert isinstance(lastname, str)
    assert isinstance(dob, str) and len(dob.split("/")) == 3
    assert isinstance(ssn, str) and len(ssn) == 4
    assert isinstance(cell, str) and len(cell.split("-")) == 3
    assert isinstance(email, str)
    assert isinstance(zipcode, str)

    driver.load("https://public.txdpsscheduler.com/")

    driver.click("English")

    driver.fill("First Name", [firstname])
    driver.fill("Last Name", [lastname])
    driver.fill("Date of Birth (mm/dd/yyyy)", dob.split("/"))
    time.sleep(0.5)
    driver.fill("Last four of SSN", [ssn])

    time.sleep(0.5)
    WebDriverWait(driver.driver, timeout=10).until(
        lambda d: "v-btn--disabled"
        not in d.find_element(
            By.XPATH, "//button[normalize-space()='Log On']"
        ).get_attribute("class")
    )

    time.sleep(1)
    driver.click("Log On")
    driver.click("New Appointment")

    time.sleep(1)
    if driver.button_exists("OK"):
        driver.click("OK")
    driver.click("Apply for first time Texas DL/Permit")

    driver.fill("Cell Phone", cell.split("-"))
    driver.fill("Email", [email])
    driver.fill("Verify Email", [email])

    els = driver.css(".v-input__slot")
    for e in els:
        if e.text == "I prefer to receive notifications via text message":
            e.click()

    driver.fill("Zip Code", [zipcode])
    els = driver.css(".button")
    for e in els:
        if "NEXT" in e.text:
            e.click()

    WebDriverWait(driver.driver, timeout=10).until(
        lambda d: d.find_elements(By.CSS_SELECTOR, ".locations") != []
    )
    els = driver.css(".locations")
    assert len(els) == 2

    appointment_table = parse_table(els[0]) + parse_table(els[1])
    return sorted(appointment_table, key=lambda x: x["date"])


@click.command()
@click.argument("config_path")
def cli(config_path):
    with open(config_path, "rb") as f:
        config = tomllib.load(f)

    print(config)

    driver = Driver(
        gui=config["settings"]["gui"], browser=config["settings"]["browser"]
    )
    current_appt_date = None

    loop = True
    while loop:
        appts = find_appointments(
            driver=driver,
            firstname=config["dmv"]["first-name"],
            lastname=config["dmv"]["last-name"],
            dob=normalize_date(config["dmv"]["birth-date"]),
            ssn=config["dmv"]["last-4-ssn"],
            cell=config["dmv"]["cell"],
            email=config["dmv"]["email"],
            zipcode=config["dmv"]["zipcode"],
        )
        print(appts)
        if config["settings"]["commit"]:
            current_appt_date = make_appointment(driver, appts[0]["date"], appts[0]["datestr"], current_appt_date, )
        loop = config["settings"]["loop"]

    driver.quit()


if __name__ == "__main__":
    cli()
