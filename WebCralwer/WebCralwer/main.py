import crochet
import time
import scrapy
import sys
# Scrapy
from scrapy import signals
from scrapy.signalmanager import dispatcher
from scrapy.crawler import Crawler, CrawlerRunner
from scrapy.settings import Settings
from scrapy.utils.log import configure_logging
from scrapy.utils.project import get_project_settings
# Flask
from flask import Flask, jsonify, request
from flask_restx import Api, Resource, fields
# Torob crawler
from WebCralwer.WebCralwer import settings as torob_settings, pipelines, middlewares
from spiders import TorobSpider
# Log
from twisted.python import log

crochet.setup()  # setting up crochet to execute
# CRAWL_RUNNER = CrawlerRunner(get_project_settings())  # initialize CrawlerRunner

# Configur logging
configure_logging({"LOG_FORMAT": "%(levelname)s: %(message)s"})

# app , api
app = Flask(__name__)
api = Api(app)

# Request body
crawl_request_body = api.model('CrawlRequest', {
    'url': fields.String(required=True, description='The URL to crawl')
})


class CrawlTorob(Resource):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.crawl_complete, self.number_of_items = False, 0
        self.crawler = None  # Initialize crawler object
        self.crawl_deferred = None  # Initialize crawl deferred

    @api.expect(crawl_request_body)
    def post(self):
        try:
            data = request.get_json()
            base_url = data.get('url')

            if base_url:
                # Start the crawl
                self.crawl_torob_with_crochet(base_url)

                while not self.crawl_complete:
                    print("********************** Crawling ... **********************")
                    time.sleep(5)
                    if self.crawl_complete:
                        break

                return 'Crawling operation finished.', 200
            else:
                return 'URL parameter is missing.', 400
        except Exception as e:
            print("An error occurred in crawl endpoint:", e)

    def crawler_result(self, item, response, spider):
        # Count extracted products
        self.number_of_items += 1

    @crochet.run_in_reactor
    def crawl_torob_with_crochet(self, base_url):
        try:
            # Initialize the crawler object
            self.crawler = Crawler(TorobSpider.TorobSpider, get_project_settings())
            self.crawler.signals.connect(self.crawler_result, signal=signals.item_scraped)
            # Set a callback for when the crawl is finished
            self.crawler.signals.connect(self.finished_crawling, signal=signals.spider_closed)
            # Start crawling
            self.crawl_deferred = self.crawler.crawl(url=base_url)
            self.crawl_deferred.addCallback(self.finished_crawling)
        except Exception as e:
            print("An error occurred in crawl_torob_with_crochet:", e)

    def finished_crawling(self, *args, **kwargs):
        print("********************** Finished crawling **********************")
        self.crawl_complete = True
        # Disconnect signals when finished crawling
        if self.crawler:
            self.crawler.signals.disconnect(self.crawler_result, signal=signals.item_scraped)


api.add_resource(CrawlTorob, "/crawl-torob")


@api.route('/test')
class Test(Resource):
    @staticmethod
    def get():
        return {'Test': 'Success'}


if __name__ == '__main__':
    app.run(debug=True)
