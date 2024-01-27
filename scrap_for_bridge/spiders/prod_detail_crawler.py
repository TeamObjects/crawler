import scrapy
import re
import time
import json
from scrap_for_bridge.items import ProductInfoDetailItem
from bs4 import  BeautifulSoup

class ProdDetailCrawlerSpider(scrapy.Spider):
    name = 'prod_detail_crawler'
    def __init__(self):
        self.count = 0
        # todo 엑셀에서 카테고리 정보랑 url 매칭해서 가져오기
        self.url = ["https://www.coupang.com/np/categories/498705",
                    "https://www.coupang.com/np/categories/498706",
                    "https://www.coupang.com/np/categories/498709"]
      
    def start_requests(self):
        for req_url in self.url:
            yield scrapy.Request(url=req_url+'?listSize=60&page=1', callback = self.parse_item_urls)
        # test
        # yield scrapy.Request(url="https://www.coupang.com/np/categories/498705?listSize=60&brand=&offerCondition=&filterType=&isPriceRange=false&minPrice=&maxPrice=&page=1&channel=user&fromComponent=Y&selectedPlpKeepFilter=&sorter=bestAsc&filter=&component=498605&rating=0", callback = self.parse_item_urls)
        # yield scrapy.Request(url="https://www.coupang.com/vp/products/7559442913?itemId=19912316479&vendorItemId=87012219573&sourceType=CATEGORY&categoryId=498605&isAddedCart="
        #                      , callback = self.parse_item_info,
        #                      meta = {
        #                         "detail_api" : f'https://www.coupang.com/vp/products/7559442913/items/19912316479/vendoritems/87012219573',
        #                         "ctgr3_name" : '티셔츠'
        #                      })
    

    def parse_item_urls(self, response):
        item_urls = response.xpath('//a[@class="baby-product-link"]/@href').getall()
        #productid , 상품번호 뒷자리, vendoritemid 로 api 만들기
        #https://www.coupang.com/vp/products/7511063437/items/19680379097/vendoritems/86785766766
        product_ids = response.xpath('//a[@class="baby-product-link"]/@data-product-id').getall()
        item_ids = response.xpath('//a[@class="baby-product-link"]/@data-item-id').getall()
        v_item_ids = response.xpath('//a[@class="baby-product-link"]/@data-vendor-item-id').getall()
        self.count +=1

        for i,item_url in enumerate(item_urls):
            yield scrapy.Request(
                url = 'https://www.coupang.com'+item_url ,
                callback = self.parse_item_info,
                meta = {
                    "detail_api" : f'https://www.coupang.com/vp/products/{product_ids[i]}/items/{item_ids[i]}/vendoritems/{v_item_ids[i]}',
                    "ctgr3_name" : response.xpath('//h3[@class="newcx-product-list-title"]/text()').get().strip()
                })
        
        #pagenation
        if ~(bool(re.search(r'(&page=1)',response.request.url))):
            for i in range(2,5):
                print(response.request.url)
                page_url = re.sub(r'(&page=1)',f'&page={i}',response.request.url)
                print(f'{i} PAGE STAT=====================')
                yield scrapy.Request(
                    url = page_url,
                    callback = self.parse_item_urls
                )

        
    def parse_item_info(self,response):
        #상품 이미지 가져오기, 첫번째 이미지가 메인이미지
        item_img_urls = response.xpath('//div[@id="repImageContainer"]//img//@data-src').getall()
        item_img_urls = ['http:'+re.sub(r'\/48x48ex\/','/492x492ex/',url) for url in item_img_urls]
        
        # 상품명 가져오기
        product_name = re.sub(r' ','_',response.xpath('//h2[@class="prod-buy-header__title"]//text()').get())
        # 상품 가격 가져오기
        if (response.xpath('//span[@class="origin-price"]/text()').get()!=None):
            price = int(re.sub(r'\,|원| ','',response.xpath('//span[@class="origin-price"]/text()').get()))
            dc_rate = int(re.sub(r'\%','',response.xpath('//span[@class="discount-rate"]/text()').get()))
        else:
            price = int(re.sub(r'\,|원','',response.xpath('//span[@class="total-price"]/strong/text()').get()))
            dc_rate = 0
        # 태그 정보 가져오기
        tags_str = response.xpath('//li[@class="prod-attr-item"]/text()').getall()
        tags_obj = [{t_str.split(': ')[0] : t_str.split(': ')[1]} for t_str in tags_str]
        
        #상품 상세설명 이미지 가져오기
        yield scrapy.Request(url = response.meta['detail_api'], 
            meta = {
                "item_img_urls" : item_img_urls,
                "product_name" : product_name,
                "price" : price,
                "dc_rate" : dc_rate,
                "tags_obj": tags_obj,
                "ctgr3_name" : response.meta['ctgr3_name']
            },
            callback = self.parse_detail_urls)
        
    def parse_detail_urls(self,response):
        #상품 상세설명 이미지 urls 가져오기
        detail_json = json.loads(response.text)['details']
        detail_urls = []
        for detail_url in detail_json:
            # 상세페이지 이미지 인거만 다운로드
            if detail_url['vendorItemContentDescriptions'][0]['imageType']:
                detail_urls.append("https:"+detail_url['vendorItemContentDescriptions'][0]['content'])
            elif detail_url['vendorItemContentDescriptions'][0]['detailType'] == 'TEXT':
                # html parsing
                soup = BeautifulSoup(detail_url['vendorItemContentDescriptions'][0]['content'],'html.parser')
                images = soup.find_all('img')
                for img in images:
                    if img.has_attr('src'):
                        detail_urls.append(img['src'])
           
        doc = ProductInfoDetailItem()
        doc['product_name'] = response.meta['product_name']
        doc['item_img_urls'] = response.meta['item_img_urls']
        doc['detail_urls'] = detail_urls
        doc['dc_rate'] = response.meta['dc_rate']
        doc['tags_obj'] = response.meta['tags_obj']
        doc['price'] = response.meta['price']
        doc['ctgr1'] = "여성패션"
        doc['ctgr2'] = "의류"
        doc['ctgr3'] = re.sub('/','_',response.meta['ctgr3_name'])
        yield doc
                    