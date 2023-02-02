from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule


class SportSpider(CrawlSpider):  # noqa
    name = 'sport'
    # allowed_domains = ['.*']
    start_urls = ['http://espn.com/nfl', 'http://bbc.com/sport/football']

    rules = (
        Rule(LinkExtractor(r"(sport|football|nfl|team|player)"), callback='parse_item', follow=True),
    )

    def parse_item(self, response):  # noqa
        item = {'url': response.url,
                'title': response.xpath('head/title/text()').get()}
        # item['domain_id'] = response.xpath('//input[@id="sid"]/@value').get()
        # item['name'] = response.xpath('//div[@id="name"]').get()
        # item['description'] = response.xpath('//div[@id="description"]').get()
        return item
