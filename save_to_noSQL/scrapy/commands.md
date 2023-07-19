1. **To create project:**
```bash
scrapy startproject <project_name> <project_entry_point>
```
project_entry_point - root point of project, <br>
project_name - name of the project.

2. **To create spider for data scraping:**
```bash
scrapy genspider <spider_name> <domain_name>
```
spider_name - make up this name (typically by domain name), <br>
domain_name - 2d and below level of domain name (without `www`).

3. **To run scraper:**
```bash
scrapy crawl <spider_name>
```


