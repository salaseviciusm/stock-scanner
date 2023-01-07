

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

    await page.waitForXPath('//div[contains(text(), "Stocks")]')
    elem = await page.xpath('//div[contains(text(), "Stocks")]')
    await elem[0].click()

    await page.waitForXPath('//span[contains(text(), "Apple")]')
    time.sleep(5)

    scroll_area = (await page.querySelectorAll('div.scrollable-area'))[1]
    prev_scroll_height = 0
    scrolled_to_end = False
    while not scrolled_to_end:
        stocks = await page.querySelectorAll('div.item-wrapper')

        scroll = 0
        for i, stock in enumerate(stocks):
            if i >= len(stocks) - 3:
                break

            elem = await stock.querySelector('div.symbol')
            ticker = await page.evaluate('(e) => e.textContent', elem)

            f_name = ticker.replace('/', '-')

            if os.path.exists(f"../stocks/{f_name}.json"):
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

            # if i == len(stocks) - 1:
            #     style = await page.evaluate('(e) => e.getAttribute("style")', stock)
            #     scroll = int(re.search(r'(?<=top: )\d+', string=style).group()) + int(re.search(r'(?<=height: )\d+', string=style).group())

            ticker_to_description[ticker] = description
            print(ticker)
            print(description)
            print("-------------------------------")

            with open(f'../stocks/{f_name}.json', 'w') as f:
                json.dump({ticker: description}, f)

            time.sleep(1.5)

        scroll_height = await page.evaluate('(e) => e.scrollHeight', scroll_area)
        scrolled_to_end = scroll_height == prev_scroll_height
        prev_scroll_height = scroll_height

        await page.evaluate(f'(e) => e.scrollTop += e.offsetHeight*3/4', scroll_area)
        time.sleep(5)

    with open('../stock-descriptions.json', 'w') as f:
        json.dump(ticker_to_description, f)


    time.sleep(50)


asyncio.get_event_loop().run_until_complete(main())
