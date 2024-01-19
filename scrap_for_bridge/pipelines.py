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
                writer2.writerow(['ctgr1','ctgr2','ctgr3','product_name','main_img','item_img_path','dc_rate','price','tags_obj','detail_imgs'])
        
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
            coupang_prod_id = re.sub(r' \- ','_',item['tags_obj'][-1]['쿠팡상품번호'])
            
            # download path 설정 (os 경로+ category_path + 상품 title.replace("/","_").replace(".","_") + 상품id)
            img_folder_path = f"../data/{ctgr1}/{ctgr2}/{ctgr3}/{product_name}/{coupang_prod_id}"
            # 상품 이미지 저장 폴더 생성
            self.make_dirs(img_folder_path)
            
            for i,img_url in enumerate(img_urls):
                # main 이미지일 경우 경로 다르게 하기
                if i == 0 :
                    #상품 상세 이미지 다운로드
                    for detail_url in item['detail_urls']:
                        self.img_req(detail_url,self.make_dirs(img_folder_path+'/details'))
                    #main 이미지 다운로드
                    main_img_path = img_folder_path + '/main_img'
                    img_folder_path = self.make_dirs(main_img_path)
                else:
                    img_folder_path = img_folder_path = f"../data/{ctgr1}/{ctgr2}/{ctgr3}/{product_name}/{coupang_prod_id}"
                result = self.img_req(img_url,img_folder_path)
                #상품 데이터 정보 tsv 저장
                if result:
                    with open(f'{self.item_info_file_name}.tsv','a',encoding='utf-8',newline='') as item_info_file:
                        writer2 = csv.writer(item_info_file,delimiter='\t')
                        #'ctgr1','ctgr2','ctgr3','product_name','main_img','item_img_path','dc_rate','price','tags_obj','detail_imgs'
                        writer2.writerow([ctgr1,ctgr2,ctgr3,product_name,main_img_path,img_folder_path,item['dc_rate'],item['price'],item['tags_obj'],img_folder_path+'/details'])
                else:
                    # 실패시 만들어 놓은 디렉토리 삭제
                    print("========================실패==========================",product_name)
                    os.rmdir(img_folder_path)

            if os.path.isdir(img_folder_path):
                ctgr_items = '>'.join([ctgr1,ctgr2,ctgr3])
                self.items_count[ctgr_items] += 1

    def change_word(self,word):
        word = word.replace(' ','')
        # 특수문자 변경
        return re.sub('[-=+,#/\?:^$.@*\"※~&%ㆍ!』\\‘|\(\)\[\]\<\>`\'…》·💕⭐]', '_', word)
    
    
    def img_req(self,img_url,img_folder_path,retries=0):
        file_name, _ = os.path.splitext(img_url)
        # file 이름 jpg 확장자로 통일하기위한 작업
        file_name = file_name.split('/')[-1].split('=')[-1]+'.jpg'
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

    def make_dirs(self,path):
        if not os.path.exists(path):
            os.makedirs(path)
        return path
    
    def close_spider(self,spider):
        print('\n===== Crawling Summary =====')

        for key, val in self.items_count.items():
            print(f'  {key} category: {val} items.')