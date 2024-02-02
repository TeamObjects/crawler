# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ScrapForBridgeItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


#상품정보에 들어갈 data
class ProductInfoDetailItem(scrapy.Item):
    # define the fields for your item here like:
    # 상품명
    product_name = scrapy.Field()
    # item img urls
    item_img_urls = scrapy.Field()
    # 상세 설명 urls
    detail_urls = scrapy.Field()
    # 할인율
    dc_rate = scrapy.Field()
    # 태그 옵션정보
    tags_obj = scrapy.Field()
    # 가격
    price = scrapy.Field()
    # depth1
    ctgr1 = scrapy.Field()
    # depth2
    ctgr2 = scrapy.Field()
    # depth3
    ctgr3 = scrapy.Field()
    # option 정보
    option_info = scrapy.Field()

# 카테고리 정보에 들어갈 data
class CtgrInfoItem(scrapy.Item):
    # 마지막 카테고리 url 정보
    third_depth_url = scrapy.Field()
    # depth1
    ctgr1_name = scrapy.Field()
    # depth2
    ctgr2_name = scrapy.Field()
    # depth3
    ctgr3_name = scrapy.Field()

#파일 title 동적으로 바꾸기 위한 변수
class CsvTitleItem(scrapy.Item):
    target_ctgr = scrapy.Field()