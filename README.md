A web crawler, Used for crawling e-commerce  websites to fetch data like product price, image, and seller ....

## Installing / Getting Started

A quick introduction of the minimal setup you need to get the service up &
running.

```shell
python -m venv venv
```

## Activate venv : 
Linux:
```shell
source venv/bin/activate
```

windows:
```shell
venv/bin/activate
```

## Installing scrapy 

```shell
pip install scrapy
```

## Installing psycopg2 to connect to a Postgres database 

```shell
pip install psycopg2
```

Then set your connection string in the following images (one for data seeding and the other for data insertion):

Date seeding

```
  self.connection = psycopg2.connect(
                host='localhost',
                user='docker',
                password='docker',
                database='crawler_db'
            )
```

Data insertion
```
self.engine = create_engine('postgresql://docker:docker@localhost/crawler_db')
```


## Installing sqlalchemy to work with data and data insertion

```shell
pip install sqlalchemy
```


## Installing flask to provide API endpoints

```shell
pip install flask
pip install flask_restx
```

## Update :

I have added the requirements.txt to make installing the needed packages easier

and also I have added Dockerfile with the docker-compose to containerize the project

Simply run the following command in the directory which the docker-compose file exists

```shell
docker-compose up
```

## For starters pass the following link to the /crawl-torob endpoint

https://api.torob.com/v4/base-product/search/?page=1&sort=popularity&size=10&category_name=%D9%85%D9%88%D8%A8%D8%A7%DB%8C%D9%84-%D9%88-%DA%A9%D8%A7%D9%84%D8%A7%DB%8C-%D8%AF%DB%8C%D8%AC%DB%8C%D8%AA%D8%A7%D9%84&category_id=175&category=175&source=next_desktop&suid=66191da888517ca4b24c6853&_bt__experiment=&_url_referrer=

