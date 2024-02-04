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
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'Host' : 'www.coupang.com'
        }
      
    def start_requests(self):
        for req_url in self.url:
            yield scrapy.Request(url=req_url+'?listSize=60&page=1', 
                                 meta={"categoryId": req_url.split('categories/')[1]},
                                 callback = self.parse_item_urls)
        # test
        # yield scrapy.Request(url="https://www.coupang.com/np/categories/498705?listSize=60&brand=&offerCondition=&filterType=&isPriceRange=false&minPrice=&maxPrice=&page=1&channel=user&fromComponent=Y&selectedPlpKeepFilter=&sorter=bestAsc&filter=&component=498605&rating=0", callback = self.parse_item_urls)
        # yield scrapy.Request(url="https://www.coupang.com/vp/products/7559442913?itemId=19912316479&vendorItemId=87012219573&sourceType=CATEGORY&categoryId=498605&isAddedCart="
        #                      , callback = self.parse_item_info,
        #                      meta = {
        #                         "detail_api" : f'https://www.coupang.com/vp/products/7559442913/items/19912316479/vendoritems/87012219573',
        #                         "ctgr3_name" : '티셔츠'
        #                      })
    

    def parse_item_urls(self, response):
        #productid , 상품번호 뒷자리, vendoritemid 로 api 만들기
        #https://www.coupang.com/vp/products/7511063437/items/19680379097/vendoritems/86785766766
        product_ids = response.xpath('//a[@class="baby-product-link"]/@data-product-id').getall()
        item_ids = response.xpath('//a[@class="baby-product-link"]/@data-item-id').getall()
        v_item_ids = response.xpath('//a[@class="baby-product-link"]/@data-vendor-item-id').getall()
        category_id = response.meta['categoryId']
        self.count +=1

        for i,product_id in enumerate(product_ids):
            yield scrapy.Request(
                url = f'https://www.coupang.com/vp/products/{product_id}?itemId={item_ids[i]}&vendorItemId={v_item_ids[i]}&sourceType=CATEGORY&categoryId={category_id}' ,
                callback = self.parse_item_info,
                headers = self.headers,
                meta = {
                    "detail_api" : f'https://www.coupang.com/vp/products/{product_id}/items/{item_ids[i]}/vendoritems/{v_item_ids[i]}',
                    "metaItem": True,
                    "category_id": category_id,
                    "ctgr3_name" : response.xpath('//h3[@class="newcx-product-list-title"]/text()').get().strip()
                })
        
        #pagenation
        if ~(bool(re.search(r'(&page=1)',response.request.url))):
            for i in range(2,5):
                page_url = re.sub(r'(&page=1)',f'&page={i}',response.request.url)
                print(f'{i} PAGE STAT=====================')
                yield scrapy.Request(
                    url = page_url,
                    callback = self.parse_item_urls,
                    meta={"categoryId":category_id}
                )
        

        
    def parse_item_info(self,response):
        #js parsing
        script_list = response.xpath('//script/text()').getall()
        if "exports.sdp = " in script_list[3] :
            res_obj = json.loads(script_list[3].split("exports.sdp = ")[1].split("};")[0] + '}')
        elif "exports.product = " in script_list[1]:
            res_obj = json.loads(script_list[1].split("exports.product = ")[1].split("};")[0] + '}')
        elif "exports.sdp = " in script_list[0]:
            res_obj = json.loads(script_list[0].split("exports.sdp = ")[1].split("};")[0] + '}')
            
        
        #상품 이미지 가져오기, 첫번째 이미지가 메인이미지
        item_img_urls = ['https:'+ url['detailImage'] for url in res_obj['images']]
        
        # 상품명 가져오기
        product_name = re.sub(r' ','_',res_obj['itemName'])
        
        # 상품 가격 & 할인정보 가져오기
        price_info = res_obj['quantityBase'][0]['price']
        
        # 할인율이 null 값일 때 처리
        if price_info.get('discountRate'):
            dc_rate = int(price_info.get('discountRate'))
            price = int(re.sub(r'\,','',price_info.get('originPrice')))
        else:
            dc_rate = 0
            price = int(re.sub(r'\,','',price_info.get('finalPrice')))
        
        # 태그 정보 가져오기
        tags_str = res_obj['sellingInfoVo']['sellingInfo']
        tags_obj = {t_str.split(': ')[0] : t_str.split(': ')[1] for t_str in tags_str}
        
        # 옵션 정보 처리하기
        '''
        [{'optionType': '사이즈',
        'attributes': {'48849201': 'S',
        '48849195': 'M',
        '48849194': 'L',
        '1514325462': 'XL',
        '3994416810': 'XXL'}},
        {'optionType': '색상',
        'attributes': {'1447883647': 'TYPE 01',
        '1447883648': 'TYPE 02',
        '1447883649': 'TYPE 03',
        '1447883650': 'TYPE 04',
        '1447883651': 'TYPE 05',
        '1447883652': 'TYPE 06',
        '1447883653': 'TYPE 07',
        '1447883655': 'TYPE 09',
        '1447883677': 'TYPE 10'}}]
        '''
        if res_obj.get('options') is not None:
            options = [{'optionType': option['name'],
                        'attributes': {
                                attr['valueId'] : attr['name']
                                for attr in option['attributes']}
                        } for option in res_obj['options']['optionRows']]
            
            option_info = self.find_option(options,res_obj)
            
            # 첫 상품 아이템만 돌리기
            if bool(response.meta['metaItem']):
                # 옵션값 조합해서 옵션 item 가져오기
                option_cond = self.make_option_cond(options)
                option_items = list(filter(None,[res_obj['options']['attributeVendorItemMap'].get(cond) for cond in option_cond]))
                for option_item in option_items:
                    # 첫상품 중복 요청 안하게 분기처리
                    if res_obj['itemId'] != option_item['itemId']:
                        yield scrapy.Request(
                            url = f'https://www.coupang.com/vp/products/{res_obj["productId"]}?itemId={option_item["itemId"]}&vendorItemId={option_item["vendorItemId"]}&sourceType=CATEGORY&categoryId={response.meta["category_id"]}' ,
                            callback = self.parse_item_info,
                            headers = self.headers,
                            meta = {
                                "detail_api" : f'https://www.coupang.com/vp/products/{res_obj["productId"]}/items/{option_item["itemId"]}/vendoritems/{option_item["vendorItemId"]}',
                                "metaItem": False,
                                "ctgr3_name" : response.meta['ctgr3_name']
                            })
        else:
            option_info = ''
        
        #상품 상세설명 이미지 가져오기
        yield scrapy.Request(url = response.meta['detail_api'], 
            meta = {
                "item_img_urls" : item_img_urls,
                "product_name" : product_name,
                "price" : price,
                "dc_rate" : dc_rate,
                "tags_obj": tags_obj,
                "ctgr3_name" : response.meta['ctgr3_name'],
                "option_info" : option_info
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
        doc['option_info']=response.meta['option_info']
        doc['ctgr1'] = "여성패션"
        doc['ctgr2'] = "의류"
        doc['ctgr3'] = re.sub('/','_',response.meta['ctgr3_name'])
        yield doc
        
    def find_option(self,options,res_obj):
        option_info = '' 
        option_obj = {}
        # 옵션값 조합해서 옵션 item 가져오기
        option_cond = self.make_option_cond(options)
        option_items = list(filter(None,[res_obj['options']['attributeVendorItemMap'].get(cond) for cond in option_cond]))
        for i,option_item in enumerate(option_items):
            if res_obj['itemId'] == option_item['itemId']:
                option_info+=option_cond[i]
        option_info_list = option_info.split(':')
        for i,option in enumerate(options):
            option_obj[option['optionType']] = option['attributes'][option_info_list[i]]
        return option_obj
    
    def make_option_cond(self, options):
        # 옵션 종류 2개 이상이면 첫번째 id : 두번째 id 이렇게 조합
        # 옵션 종류 1개면 그냥 valueid 하나값으로 조회
        # x축 기본으로 그리고, y축은 2차원 배열일때 추가해서 조합
        cond = []
        x_options = list(options[0]['attributes'].keys())
        for x_option in x_options:
            if len(options) == 2 :
                for y_option in options[1]['attributes'].keys():
                    cond.append(x_option+":"+y_option)
            else:
                cond.append(x_option)
        return cond