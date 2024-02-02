# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from urllib.request import urlretrieve
from urllib.error import HTTPError
import os
import csv
import time
import re
import datetime
from .items import CtgrInfoItem, ProductInfoDetailItem
from collections import defaultdict

class ScrapForBridgePipeline:
    def __init__(self):
        self.start_time = datetime.date.today().strftime("%y%m%d")
        self.make_dirs('../data')
        self.items_count = defaultdict(int)
        self.ctgr_info_file_name = os.path.join("../data/", f'카테고리정보_{self.start_time}')
        self.item_info_file_name = os.path.join("../data/", f'상품정보_{self.start_time}')
        
        #카테고리 정보 tsv 파일 생성
        with open(f'{self.ctgr_info_file_name}.tsv', 'a',encoding='utf-8', newline='') as ctgr_info_file:
            writer = csv.writer(ctgr_info_file, delimiter='\t')
            writer.writerow(['1뎁스 이름', '2뎁스 이름','3뎁스 이름','3뎁스 url'])
        #상품 정보 tsv 파일 생성
        with open(f'{self.item_info_file_name}.tsv','a',encoding='utf-8', newline='') as item_info_file:
                writer2 = csv.writer(item_info_file, delimiter='\t')
                writer2.writerow(['ctgr1','ctgr2','ctgr3','product_name','img_type','img_seq_no','dc_rate','price','tags_obj','img_path','option_info','img_url'])
        
    def process_item(self, item, spider):
        # 카테고리 정보 넘어올 때 실행
        if isinstance(item,CtgrInfoItem):
            print(f'processing, {item["ctgr3_name"]}')
            with open(f'{self.ctgr_info_file_name}.tsv', 'a',encoding='utf-8', newline='') as ctgr_info_file:
                writer = csv.writer(ctgr_info_file, delimiter='\t')
                writer.writerow([item['ctgr1_name'], item['ctgr2_name'],item['ctgr3_name'],item['third_depth_url']])
        
        # 상품 정보 저장 파이프라인
        if isinstance(item,ProductInfoDetailItem):
            print(f'processing, {item["product_name"]}')
            img_urls = item['item_img_urls']
            product_name = self.change_word(item['product_name'])
            ctgr1 = item['ctgr1']
            ctgr2 = item['ctgr2']
            ctgr3 = item['ctgr3']
            coupang_prod_id = re.sub(r' \- ','_',item['tags_obj']['쿠팡상품번호'])
            # download path 설정 (os 경로+ category_path + 상품 title.replace("/","_").replace(".","_") + 상품id)
            img_folder_path = f"../data/{ctgr1}/{ctgr2}/{ctgr3}/{product_name}/{coupang_prod_id}"
            # 상품 이미지 저장 폴더 생성
            self.make_dirs(img_folder_path)
            xlxs_info = {}
            # 공통데이터 작업
            xlxs_info["ctgr1"] = ctgr1
            xlxs_info["ctgr2"] = ctgr2
            xlxs_info["ctgr3"] = ctgr3
            xlxs_info["product_name"] = product_name
            xlxs_info["img_folder_path"] = img_folder_path
            xlxs_info["dc_rate"] = item["dc_rate"]
            xlxs_info["price"] = item["price"]
            xlxs_info["tags_obj"] = item["tags_obj"]
            xlxs_info["option_info"] = item["option_info"]
            
            for i,img_url in enumerate(img_urls):
                #상품 상세 이미지 다운로드
                for j,detail_url in enumerate(item['detail_urls']):
                    xlxs_info["img_type"] = 'detail'
                    xlxs_info["img_seq_no"] = j+1
                    detail_folder_path = f"../data/{ctgr1}/{ctgr2}/{ctgr3}/{product_name}/{coupang_prod_id}/details"
                    xlxs_info["img_file_name"] = detail_folder_path +'/'+ self.extract_filename(img_url)
                    xlxs_info["img_url"] = img_url
                    self.record_info(self.img_req(detail_url,self.make_dirs(detail_folder_path)),xlxs_info)
                    
                #사진 순서
                xlxs_info["img_seq_no"] = i+1
                # main 이미지일 경우 경로 다르게 하기
                if i == 0 :
                    #main 이미지 다운로드
                    xlxs_info["img_type"] = 'main'
                    main_img_path = img_folder_path + '/main_img'
                    xlxs_info["img_file_name"] = main_img_path +'/'+ self.extract_filename(img_url)
                    img_folder_path = self.make_dirs(main_img_path)
                else:
                    xlxs_info["img_type"] = 'product'
                    img_folder_path = f"../data/{ctgr1}/{ctgr2}/{ctgr3}/{product_name}/{coupang_prod_id}"
                    xlxs_info["img_file_name"] = img_folder_path +'/'+ self.extract_filename(img_url)
                xlxs_info["img_url"] = img_url
                self.record_info(self.img_req(img_url,img_folder_path),xlxs_info)


            if os.path.isdir(img_folder_path):
                ctgr_items = '>'.join([ctgr1,ctgr2,ctgr3])
                self.items_count[ctgr_items] += 1

    def change_word(self,word):
        word = word.replace(' ','')
        # 특수문자 변경
        return re.sub('[-=+,#/\?:^$.@*\"※~&%ㆍ!』\\‘|\(\)\[\]\<\>`\'…》·💕⭐]', '_', word)
    
    def record_info(self,result,xlxs_info):
        ctgr1 = xlxs_info["ctgr1"]
        ctgr2 = xlxs_info["ctgr2"]
        ctgr3 = xlxs_info["ctgr3"]
        product_name = xlxs_info["product_name"]
        img_type = xlxs_info["img_type"]
        img_seq_no = xlxs_info["img_seq_no"]
        dc_rate = xlxs_info["dc_rate"]
        price = xlxs_info["price"]
        tags_obj = xlxs_info["tags_obj"]
        img_file_name = xlxs_info["img_file_name"]
        img_folder_path = xlxs_info["img_folder_path"]
        option_info = xlxs_info["option_info"]
        img_url = xlxs_info["img_url"]
        #상품 데이터 정보 tsv 저장
        if result:
            with open(f'{self.item_info_file_name}.tsv','a',encoding='utf-8',newline='') as item_info_file:
                writer2 = csv.writer(item_info_file,delimiter='\t')
                #'ctgr1','ctgr2','ctgr3','product_name','img_type','img_seq_no','dc_rate','price','tags_obj','img_file_name'
                writer2.writerow([ctgr1,ctgr2,ctgr3,product_name,img_type,img_seq_no,dc_rate,price,tags_obj,img_file_name,option_info,img_url])
        else:
            # 실패시 만들어 놓은 디렉토리 삭제
            print("========================실패==========================",product_name)
            os.rmdir(img_folder_path)
        
    def img_req(self,img_url,img_folder_path,retries=0):
        file_name = self.extract_filename(img_url)
        try:
            result = urlretrieve(img_url,os.path.join(img_folder_path,file_name))
            # 3번 더 retry 
            if result == False and retries <= 3:
                print(result)
                time.sleep(3)
                retries +=1
                self.img_req(img_url,img_folder_path,file_name,retries)
            return result
        except HTTPError as e:
            if e.code == 404:
                #3번 했는데 계속 나오는 건 no image로 판단. pass
                if retries > 3 : return print(f'[img_folder_path] : {img_folder_path} , [img_url] : {img_url}')
                time.sleep(3)
                retries +=1
                self.img_req(img_url,img_folder_path,file_name,retries)
            else:
                return None
            
    def extract_filename(self,img_url):
        file_name, _ = os.path.splitext(img_url)
        # file 이름 jpg 확장자로 통일하기위한 작업
        return file_name.split('/')[-1].split('=')[-1]+'.jpg'
        
        
    def make_dirs(self,path):
        if not os.path.exists(path):
            os.makedirs(path)
        return path
    
    def close_spider(self,spider):
        print('\n===== Crawling Summary =====')

        for key, val in self.items_count.items():
            print(f'  {key} category: {val} items.')