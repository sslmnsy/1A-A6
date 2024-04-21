import scrapy

class MangaScraper(scrapy.Spider):
    name = "mangaspider"
    start_urls = ["https://myanimelist.net/topmanga.php"]
    page = 0
    scraped_count = 0  # Variabel untuk menghitung jumlah data yang telah diambil
    results = []  # List untuk menyimpan data scraping manga

    def parse(self, response):
        for index, mangas in enumerate(response.css('tr.ranking-list'), start=self.scraped_count + 1):
            link = mangas.css('a.hoverinfo_trigger::attr(href)').get()
            yield response.follow(link, callback=self.parse_manga_page, meta={'rank': str(index)})

            self.scraped_count += 1  # Menambahkan jumlah data yang telah diambil

            # Berhenti jika sudah mencapai 100 data
            if self.scraped_count >= 100:
                return

        next_page = response.css('a.link-blue-box.next::attr(href)').get()
        if next_page is not None and self.scraped_count < 100:
            next_page_url = response.urljoin(next_page)
            self.page += 1
            yield response.follow(next_page_url, callback=self.parse)

    def parse_manga_page(self, response):
        title = response.css('span[itemprop="name"]::text').get()
        image_url = response.css('div.leftside > div:first-child > a > img::attr(data-src)').get()
        rank = response.meta['rank']  # Menggunakan rank yang diambil dari meta
        popularity = response.css('span.numbers.popularity > strong::text').get()
        rating = response.css('div.score-label::text').get()
        genres = response.css('span[itemprop="genre"]::text').getall()
        publish = response.xpath('//div[contains(span[@class="dark_text"], "Published:")]/text()').get()
        authors = response.xpath('//div[@class="spaceit_pad"]/span[@class="dark_text"][contains(text(), "Authors")]/following-sibling::a/text()').getall() 
        characters = [
        name.replace('\n', '').strip().replace(',', '')  
        if ',' not in name else ' '.join(reversed(name.split(', '))) 
        for name in response.css('div.detail-characters-list.clearfix a[href*="/character/"]::text').getall() if name.strip()
    ]
        # Ekstrak synopsis dan status
        info = response.xpath('//span[contains(text(), "Status:")]/following-sibling::text()').getall()
        status = info[0].strip() if info else None
        synopsis = response.css('span[itemprop="description"]::text').get()

        item = {
            'rank': rank,
            'title': title.strip() if title else None,
            'url': response.url,
            'image_url': image_url,
            'rating': rating.strip() if rating else None,
            'popularity': popularity.replace("#", "").strip() if popularity else None,
            'genres': [genre.strip() for genre in genres] if genres else None,
            'publish': publish[:14].strip().replace("  ", " ") if publish else None,
            'authors': [author.strip() for author in authors] if authors else None,
            'characters': characters,
            'status': status,
            'synopsis': synopsis,
        }

        self.results.append(item)  # Append scraped manga data to results list
        yield item  # Yield the scraped manga item

    def closed(self, reason):
        # Sort the results by rank
        sorted_results = sorted(self.results, key=lambda x: int(''.join(filter(str.isdigit, x['rank']))))
        # Output the sorted results as JSON
        with open('manga_data.json', 'w') as f:
            import json
            json.dump(sorted_results, f, indent=4)
