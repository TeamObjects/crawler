import scrapy
from scrap_for_bridge.items import CtgrInfoItem

class CoupangCateCrawlerSpider(scrapy.Spider):
    name = 'coupang_cate_crawler'
    allowed_domains = ['www.coupang.com']
    
    # 쿠팡 홈에서 첫 시작
    def __init__(self):
      self.url = 'https://www.coupang.com/'

    def start_requests(self):
        yield scrapy.Request(url=self.url, callback = self.parse_one_url)
    
        
    def parse_one_url(self,response):
        # 카테고리 1 depth짜리
        one_depth_urls = response.xpath(f'//a[@class="first-depth"]/@href').getall()
        # 1depth짜리 이름
        one_depth_names = response.xpath(f'//a[@class="first-depth"]//text()').getall()
        # 패션의류/잡화의 두번째 뎁스 목록 근데 원래는 1depth 였음
        fashion_urls = response.xpath(f'//li[@class="fashion-sundries"]//li[@class="second-depth-list"]/a/@href').getall()
        fashion_names = response.xpath(f'//li[@class="fashion-sundries"]//li[@class="second-depth-list"]/a//text()').getall()

        total_urls = fashion_urls + one_depth_urls
        total_names = fashion_names + one_depth_names
        
        
        for i, t_url in enumerate(total_urls):
            yield scrapy.Request(url = 'https://www.coupang.com'+t_url , 
            callback = self.parse_second_url,
            meta = {
                "one_depth_name" : total_names[i]
            })
    
    def parse_second_url(self,response):
        #url
        second_urls = response.xpath(f'//li[@data-link-uri]/@data-link-uri').getall()
        #name
        second_names = response.xpath(f'//li[@data-link-uri]//label//text()').getall()
        
        for i, s_url in enumerate(second_urls):
            yield scrapy.Request(url = 'https://www.coupang.com'+s_url , 
            callback = self.parse_last_url,
            meta = {
                "one_depth_name" : response.meta['one_depth_name'],
                "two_depth_name" : second_names[i]
            })
    
    def parse_last_url(self,response):
        #3depth urls
        third_urls = response.xpath(f'//ul[@class="search-option-items-child"]//@data-link-uri').getall()
        #3depth names
        third_names = response.xpath(f'//ul[@class="search-option-items-child"]//label//text()').getall()
        # 카테고리 정보 객체에 담기
        doc = CtgrInfoItem()
        for i, th_url in enumerate(third_urls):
            doc['third_depth_url'] = 'https://www.coupang.com'+th_url
            doc['ctgr1_name'] = response.meta['one_depth_name']
            doc['ctgr2_name'] = response.meta['two_depth_name']
            doc['ctgr3_name'] = third_names[i]
            yield doc