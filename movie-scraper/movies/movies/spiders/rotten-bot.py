import scrapy
import os
from selenium import webdriver
from selenium.webdriver.common.keys import Keys

chromedriver = "/usr/bin/chromedriver"
os.environ["webdriver.chrome.driver"] = chromedriver


class RottenSpider(scrapy.Spider):
    
    def __init__(self):
        self.driver = webdriver.Chrome()

    name = 'rotten_score'

    custom_settings = {
        "DOWNLOAD_DELAY": 3,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 3,
        "HTTPCACHE_ENABLED": True
    }

    start_urls = [
        'https://www.rottentomatoes.com/browse/dvd-streaming-all',
    ]

    def parse(self, response):
        
        self.driver.get(response.url)

        while True:
            next = self.driver.find_element_by_xpath('//button[@class="btn btn-secondary-rt mb-load-btn"]')

            try:
                next.click()
                    
                # Do scrapy stuff
            except:
                break    
            
        self.driver.close()

        for href in response.xpath(
            '//span[@class="festivaltitle"]/a/@href'
        ).extract():

            yield scrapy.Request(
                url=href,
                callback=self.parse_festival,
                meta={'url': href}
            )

        next_url = response.xpath(
            '//div[@class="pagination"]/ul/li/a[@class="next page-numbers"]\
            /@href'
        ).extract()[0]

        yield scrapy.Request(
            url=next_url,
            callback=self.parse
        )
