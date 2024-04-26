A web crawler, Used for crawling e-commerce  websites to fetch data like product price, image, and seller ....

## Installing / Getting Started

A quick introduction of the minimal setup you need to get a hello world up &
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




