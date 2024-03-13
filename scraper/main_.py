from bs4 import BeautifulSoup
from aiohttp import ClientSession
import asyncio
from lxml import etree


class Scraper:
    def __init__(self, season:str) -> None:
        self.season = season

        self.xpath_dict = {
            "box_scores": "//a[@class='link' and ./span[2][contains(text(), 'Box Score')]]",
            "playbyplay": "//a[contains(text(),'Play by Play')]",
            "playbyplaytab": "//span[@class='label' and contains(text(), 'Periods:')]",
            "q_element": "//table[@role='presentation']",
        }

        self.main_page = "https://universitysport.prestosports.com/"
        self.box_scores_page = f"sports/mbkb/{self.season}/schedule"

    async def get_soup(self, session, url:str) -> BeautifulSoup|None:
        # async with ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                try:
                    response = await response.text()
                    return BeautifulSoup(response, 'html.parser')
                except UnicodeDecodeError:
                    print(f"Error fetching {url}: {response.status}")
                    return None
            else:
                print(f"Error fetching {url}: {response.status}")
                return None

    def find_xpath(self, soup:BeautifulSoup, xpath:str):
        tree = etree.fromstring(str(soup), parser=etree.HTMLParser())
        elements = tree.xpath(xpath)
        return elements

    async def main(self):
        async with ClientSession() as session:
            boxes_soup = await self.get_soup(session, self.main_page + self.box_scores_page)
            links = self.find_xpath(boxes_soup, self.xpath_dict["box_scores"])

            tasks = []
            for link in links[:14]:
                link = self.main_page + link.get("href")
                task = self.get_soup(session, link)
                tasks.append(task)

            match_contents = await asyncio.gather(*tasks)
            print(match_contents[-1])

scraper = Scraper("2023-24")
asyncio.run(scraper.main())
