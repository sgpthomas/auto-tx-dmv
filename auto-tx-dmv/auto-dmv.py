#!/usr/bin/env python3

from selenium import webdriver
from selenium.common import exceptions
from selenium.webdriver import ActionChains
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
import click
import time


DATEFMT = "%m/%d/%Y"


def normalize_date(datestr):
    return time.strftime(DATEFMT, time.strptime(datestr, DATEFMT))


def make_appointment(driver, datestr):
    appts = driver.find_elements(By.CSS_SELECTOR, ".card.blue")
    for card in appts:
        print(card.text)
        if datestr in card.text:
            card.click()
            break

    slots = driver.find_elements(By.CSS_SELECTOR, ".slot-card.blue-grey")
    if len(slots) > 0:
        slots[0].click()

    els = driver.find_elements(By.CSS_SELECTOR, ".button")
    for e in els:
        if "NEXT" in e.text:
            e.click()
            break

    click_btn(driver, "Confirm")


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
            }
        ]

    return result


class Driver:
    def __init__(self, gui=True):
        options = Options()
        options.page_load_strategy = "normal"
        if not gui:
            options.add_argument("--headless")
        self.driver = webdriver.Firefox(options=options)
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

    print("Loading https://public.txdpsscheduler.com/")
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

    # # make the appointment!
    # if time.strptime(datestr, DATEFMT) < time.strptime(best_current, DATEFMT):
    #     print("Yahooo!!!!!")
    #     make_appointment(driver, datestr)
    #     current_apt_date = datestr
    # else:
    #     print("Didn't find anything sonner :(")

    # print("Finished, waiting 30 secs")
    # time.sleep(30)

    # return els


def main():
    current_apt_date = "6/2/2023"
    while True:
        try:
            pass
        except Exception as e:
            print("Crashed!", e)


@click.command()
@click.option("--name", help="Your full name, separated by spaces")
@click.option("--email", help="Your email")
@click.option("--dob", help="Date of Birth, separated by slashes")
@click.option("--cell", help="Cell phone number, separted by dashes")
@click.option("--ssn", help="Last 4 digits of Social Security Number")
@click.option("--zipcode", help="Zip code")
@click.option("--current", help="Best current appointment date")
@click.option("--loop", help="Run the script in an infinite loop", is_flag=True)
@click.option(
    "--commit", help="Give the script permission to make appointments", is_flag=True
)
@click.option("--gui", is_flag=True)
def cli(name, email, dob, cell, ssn, zipcode, current, loop, commit, gui):
    dob = normalize_date(dob)
    current = normalize_date(current)

    driver = Driver()

    firstname, lastname = name.split(" ")
    appts = find_appointments(
        driver=driver,
        firstname=firstname,
        lastname=lastname,
        dob=dob,
        ssn=ssn,
        cell=cell,
        email=email,
        zipcode=zipcode,
    )

    print(appts)

    input()
    driver.quit()


if __name__ == "__main__":
    cli()


d = Driver()
appts = find_appointments(
    driver=d,
    firstname="Samuel",
    lastname="Thomas",
    dob="08/05/1998",
    ssn="3748",
    cell="323-360-6970",
    email="sgpthomas@gmail.com",
    zipcode="78722",
)
