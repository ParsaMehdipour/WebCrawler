import crochet
import time
from flask import Flask, jsonify, request
from flask_restx import Api, Resource, fields
from scrapy import signals
from twisted.internet import reactor
import scrapy
from scrapy.crawler import Crawler, CrawlerRunner
from scrapy.utils.log import configure_logging
from WebCralwer.WebCralwer import settings as torob_settings
from WebCralwer.WebCralwer import pipelines, middlewares
from scrapy.settings import Settings

# Import your spider here
from spiders import TorobSpider

import sys
from twisted.python import log

crochet.setup()

configure_logging({"LOG_FORMAT": "%(levelname)s: %(message)s"})

app = Flask(__name__)
api = Api(app)

crawl_request_body = api.model('CrawlRequest', {
    'url': fields.String(required=True, description='The URL to crawl')
})

output_data = []


@api.route('/hello')
class HelloWorld(Resource):
    def get(self):
        return {'hello': 'world'}


class Crawl(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scrape_complete = False

    @api.expect(crawl_request_body)
    def post(self):
        data = request.get_json()
        base_url = data.get('url')

        if base_url:
            scrape(base_url)
            print("********************** initializing the runner ...")
            # reactor.run()  # the script will block here until the crawling is finished

            while self.scrape_complete is False:
                print("********************** Crawling ...")
                time.sleep(5)

            return 'Scraping operation completed.', 200
        else:
            return 'URL parameter is missing.', 400


api.add_resource(Crawl, "/crawl")


@crochet.run_in_reactor
def scrape(base_url):
    print("Scraping {} ...".format(base_url))
    crawler_settings = Settings()
    print(crawler_settings)
    crawler_settings.setmodule(torob_settings)
    print(crawler_settings)
    runner = CrawlerRunner()
    print(runner)
    eventual = runner.crawl(TorobSpider.TorobSpider, url=base_url)
    eventual.addCallback(finished_scrape)
    return eventual


def _crawler_result(item, response, spider):
    output_data.append(dict(item))


def finished_scrape(*args, **kwargs):
    print("************************* finished scraping ...")
    Crawl.scrape_complete = True


if __name__ == '__main__':
    app.run(debug=True)
