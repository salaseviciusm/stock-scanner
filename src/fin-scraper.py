

import asyncio
import sys

from pyppeteer import launch
import time


async def login(page):
    await page.goto("https://live.trading212.com/")

    await page.waitForXPath("//p[contains(text(), 'Accept all cookies')]")
    time.sleep(1)

    elem = await page.xpath("//p[contains(text(), 'Accept all cookies')]")
    if len(elem) > 0:
        await elem[0].click()

    async def enter_details():
        await page.waitFor('input[name="email"]')
        time.sleep(1)
        email = await page.querySelector('input[name="email"]')
        await page.evaluate('(e) => e.value = "salaseviciusmorkus@gmail.com"', email)

        password = await page.querySelector('input[name="password"]')
        await page.evaluate(f'(e) => e.value = "{input("password> ")}"', password)

        login_btn = await page.querySelector('input[value="Log in"]')
        await login_btn.click()

    await enter_details()
    email2 = await page.querySelector('input[name="email"]')
    if email2 is not None:
        await enter_details()

    await page.waitFor('div.search-tab')
    elem = await page.querySelector("div.search-tab")
    return elem is not None


async def main():
    browser = await launch(headless=False)
    page = await browser.newPage()

    if not await login(page):
        print("Could not log in")
        sys.exit(1)

    search = await page.querySelector("div.search-tab")
    await search.click()

    await page.waitForXPath('//div[contains(text(), "Stocks")]')
    elem = await page.xpath('//div[contains(text(), "Stocks")]')
    await elem[0].click()

    await page.waitForXPath('//span[contains(text(), "Apple")]')
    stocks = await page.querySelectorAll('div.item-wrapper')
    print(stocks)
    time.sleep(50)


asyncio.get_event_loop().run_until_complete(main())
