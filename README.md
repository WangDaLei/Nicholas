# PBCOperationSpider
* <strong>EN:Chinese A-share Market quantitative investment system. Using Scrapy to crawl data and Django ORM to store data to database(Mysql used). We get data from sina, yahoo and some other finance web site. Now the system is under developing
* <strong>CN:</strong>中国A股量化投资系统, 使用Scrapy爬取数据，使用Django ORM模型存储数据.目前从新浪财经，雅虎财经和其他相关的财经网站中获取数据.系统目前正在开发中...

### <strong>Requrements</strong>
* The Project using [Scrapy](https://github.com/scrapy/scrapy) to crawl the web, and using [scrapy-splash](https://github.com/scrapy-plugins/scrapy-splash) to JavaScript integration. My system is Ubuntu 18.04.
* First, we install all the dependence. Make sure that python version is 3.X and mysql-server have been installed. And you should execute these commands : apt-get install libmysqlclient-dev python3-dev

    ``` 
    pip install -r requirements.txt
    ```
* After that, we start a docker container to run splash.

    if you have not install docker,you should install docker.
    ```
    sudo apt-get install docker.io    
    ```
    run these commands with root permission.
    ```
    docker pull scrapinghub/splash
    docker run -p 8050:8050 scrapinghub/splash
    ```
    splash now is running at 127.0.0.1:8050, also you can run it at remote host, if that you should modify the setting files of spider.

### <strong>Install And Run</strong>

* Then, we config and create database, In stock/settings.py we can config the database DATABASES option, more details search django document.
We create database and tables with these commands below.

    ```
    ./manage.py dbshell
    > create database stock use default charset utf8;
    > quit
    ./manage.py makemigrations
    ./manage.py migrate
    ``` 

* Then we can run the spider directly

    ```
    cd stock_spider
    scrapy crawl stock_info_spider
    scrapy crawl stock_block_spider
    scrapy crawl stock_capital_amount_spider
    scrapy crawl stock_finance_spider
    scrapy crawl stock_bonus_spider
    scrapy crawl stock_allotment_spider
    scrapy crawl stock_trade_record_task_spider
    ```
* Or we can run it with celery, which will run the spider automatic at a specific time. Redis is as the broker between celery task and worker, before that we must install Redis.
These three commands must run at three different terminals

    ```
    redis-server
    celery -A stock beat -l info
    celery -A stock worker -l info
    ```
It's Ok. Congratulations.
