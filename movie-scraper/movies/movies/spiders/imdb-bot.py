import scrapy
import re
import urllib.parse
from scrapy.loader import ItemLoader


# Scrapy version 1.4.0 needed

start_year = 1980
end_year = 2017
page_max = 10000

class IMDB_Spider(scrapy.Spider):

    def __init__(self):
        self.current_page = 1

    name = 'imdb'
    custom_settings = {
        #"DOWNLOAD_DELAY": 3,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 3,
        "HTTPCACHE_ENABLED": True
    }

    start_urls = [
        'http://www.imdb.com/search/title?sort=moviemeter,asc&title_type=feature&year={start},{end}&view=simple&page={page}&ref_=adv_nxt'.format(start=start_year, end=end_year, page=1),
    ]

    def parse(self, response):
        
        # Get list of films and parse
        for href in response.xpath(
            '//div[@class="col-title"]/span/span/a/@href'
        ).extract():

            yield response.follow(
                href,
                self.parse_film,
                meta={'url': href}
            )

        # Retrieve next page
        next_url = response.xpath('//a[@class="lister-page-next next-page"]')[0]
        if (next_url is not None) and (self.current_page <= page_max):
            self.current_page += 1
            yield response.follow(
                url= next_url,
                callback= self.parse
            )
        


    def parse_film(self, response):
        
        url = response.request.meta['url']

        title = response.xpath('//div[@class="title_wrapper"]/h1/text()').extract_first().strip()
        year = response.xpath('//span[@id="titleYear"]/a/text()').extract_first().strip()
        rating = response.xpath('//div[@class="ratingValue"]/strong/span[@itemprop="ratingValue"]/text()').extract_first()
        try:
            rating_count = response.xpath('//span[@itemprop="ratingCount"]/text()').extract_first()
        except:
            rating_count = 'NaN'
        
        mpaa_raw = response.xpath('//span[@itemprop="contentRating"]/text()').extract_first()
        if mpaa_raw.lower() == 'g' :
            mpaa = 'G'
        else:    
            mpaa = re.search('^Rated ([^\s]+)', mpaa_raw)[1].strip()
        try:
            runtime = response.xpath('//time[@itemprop="duration"]/text()').extract()[1].split()[0]
        except:
            runtime = 'NaN'
        
        try:
            director = response.xpath('//span[@itemprop="director"]/a/span/text()').extract_first()
        except:
            director = 'NaN'
        
        genre = ','.join(response.xpath('//div[@itemprop="genre"]/a/text()').extract())

        try:
            budget = response.xpath('//div[@class="txt-block" and h4/text()="Budget:"]/text()').extract()[1].strip().replace(',', '')
        except:
            budget = 'NaN'

        try:
            country = response.xpath('//div[@class="txt-block" and h4/text()="Country:"]/a/text()').extract_first()
        except:
            country = 'NaN'

        try:
            language = ','.join(response.xpath('//div[@class="txt-block" and h4/text()="Language:"]/a/text()').extract())
        except:
            language = 'NaN'

        release = response.xpath('//meta[@itemprop="datePublished"]/@content').extract_first()

        # Store results in a dictionary
        results = {
            'title':title,
            'year':year,
            'release':release,
            'rating':rating,
            'rating_count':rating_count,
            'genre':genre,
            'director':director,
            'budget':budget,
            'mpaa':mpaa,
            'runtime':runtime,
            'country':country,
            'language':language,
            'url':url
        }

        # Search for opening and gross on Box-Office Mojo    
        box_url = 'http://www.boxofficemojo.com/search/?q={}'
        # Make title URL safe
        title_url = urllib.parse.quote(title)

        # Call parsing on the Box Office Mojo page
        yield response.follow(
            box_url.format(title_url),
            self.parse_box_office_search,
            meta=results
        )




    def parse_box_office_search(self, response):

        year = response.request.meta['year']
        title = response.request.meta['title']

        # Find the relavent row where the title and year of the film are matched
        row = response.xpath('//tr[ (contains(td/b/font/a/text(), "{0}")) and \
        (contains(td/font/a[contains(@href, "schedule")]/text(), "{1}"))]'\
        .format(title,year))

        # Extract the lifetime and opening gross
        lifetime = row.xpath('td/font/text()')[1].extract()
        opening = row.xpath('td/font/text()')[3].extract()

        # Retrieve URL
        mojo_url = row.xpath('td/a/@href').extract_first()

        # Grab theaters and studio
        try:
            studio =  row.xpath('td/font/text()')[0].extract()
        except:
            studio = 'None'

        try:
            theaters = row.xpath('td/font/text()')[4].extract()
        except:
            theaters = 'None'

        results = response.request.meta
        results.update({'lifetime':lifetime,
                'opening':opening,
                'mojo_url':mojo_url,
                'studio':studio,
                'theaters':theaters
                 })

        
        
        yield response.follow(
            url = mojo_url,
            callback = self.parse_mojo_worldwide,
            meta = results
        )


    def parse_mojo_worldwide(self,response):
        
        try:
            worldwide = response.xpath('//tr[contains(td/b/text(), "Worldwide:")]/td/b/text()')\
            .extract()[1]
        except:
            worldwide = 'None'

        results = response.request.meta
        results.update({
            'worldwide':worldwide
        })

        yield results