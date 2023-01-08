

import asyncio
import sys
import os

from pyppeteer import launch
import time
import re
import json

ticker_to_description = dict()

async def login(page):
    await page.goto("https://live.trading212.com/")

    try:
        await page.waitForXPath("//p[contains(text(), 'Accept all cookies')]")
        time.sleep(1)

        elem = await page.xpath("//p[contains(text(), 'Accept all cookies')]")
        if len(elem) > 0:
            await elem[0].click()
    except:
        # await page.waitForXPath("//p[contains(text(), 'Log in')]")
        await page.querySelector('p.Header_login-button__JDAIM')
        # elem = await page.xpath("//p[contains(text(), 'Log in')]")
        elem = await page.querySelector('p.Header_login-button__JDAIM')
        await elem.click()

    async def enter_details():
        await page.waitFor('input[name="email"]')
        time.sleep(1)
        email = await page.querySelector('input[name="email"]')
        await page.evaluate('(e) => e.value = "salaseviciusmorkus@gmail.com"', email)

        password = await page.querySelector('input[name="password"]')
        await page.evaluate(f'(e) => e.value = "{os.environ["T212-password"]}"', password)

        login_btn = await page.querySelector('input[value="Log in"]')
        await login_btn.click()

    await enter_details()
    email2 = await page.querySelector('input[name="email"]')
    if email2 is not None:
        await enter_details()

    return True


async def pull_data(page, tags=None):
    if tags is None:
        tags = {}

    await page.waitFor('div.item-wrapper')
    time.sleep(5)

    scroll_area = (await page.querySelectorAll('div.scrollable-area'))[1]
    prev_scroll_height = 0
    scrolled_to_end = False
    while not scrolled_to_end:
        scroll_height = await page.evaluate('(e) => e.scrollHeight', scroll_area)
        scrolled_to_end = scroll_height == prev_scroll_height
        if scrolled_to_end:
            break
        prev_scroll_height = scroll_height

        stocks = await page.querySelectorAll('div.item-wrapper')

        for i, stock in enumerate(stocks):
            if i >= len(stocks) - 1:
                break

            elem = await stock.querySelector('div.symbol')
            ticker = await page.evaluate('(e) => e.textContent', elem)

            f_name = ticker.replace('/', '-')

            if not REPLACE_DATA and os.path.exists(f"../stocks/{f_name}.json"):
                continue

            while True:
                await stock.click()
                time.sleep(2)
                try:
                    await page.waitFor('div.description')
                    break
                except:
                    pass

            elem = await page.querySelector('div.description')
            description = await page.evaluate('(v) => v.textContent', elem)

            elem = await page.querySelector('div.close-button-in-header')
            await elem.click()

            print(ticker)
            print(description)
            print("-------------------------------")

            with open(f'../stocks/{f_name}.json', 'w') as f:
                json.dump({
                    ticker: description,
                    'tags': tags
                }, f)

            time.sleep(1.5)

        await page.evaluate(f'(e) => e.scrollTop += e.offsetHeight*3/4', scroll_area)
        time.sleep(5)


async def main():
    browser = await launch(headless=False)
    page = await browser.newPage()
    await page.setViewport({'width': 1400, 'height': 1080})

    if not await login(page):
        print("Could not log in")
        sys.exit(1)

    while True:
        try:
            search = await page.querySelector("div.search-tab")
            await search.click()
            break
        except:
            pass

    await page.waitForXPath('//div[contains(text(), "Stocks") and contains(@class, "label")]')
    elem = await page.xpath('//div[contains(text(), "Stocks") and contains(@class, "label")]')
    time.sleep(3)
    await elem[0].click()
    time.sleep(1)

    async def scrape_folder(folder, hierarchy=None):
        if hierarchy is None:
            hierarchy = []

        folder_name = await page.evaluate("(e) => e.textContent", folder)
        print(folder_name)
        hierarchy.append(folder_name)

        await folder.click()
        time.sleep(3)

        folder = await page.evaluateHandle("(e) => e.closest('div.search-folder')", folder)
        folders = await folder.asElement().querySelectorAll('div.label')
        print(len(folders[1:]))
        # First folder is the current one we are in
        if len(folders[1:]) == 0:
            await pull_data(page, tags={'hierarchy': hierarchy})
        else:
            for f in folders[1:]:
                await scrape_folder(f, hierarchy=hierarchy.copy())

    elem = await page.xpath('//div[contains(text(), "Browse all") and contains(@class, "label")]')
    await scrape_folder(elem[0])

    time.sleep(50)

REPLACE_DATA = True
asyncio.get_event_loop().run_until_complete(main())
