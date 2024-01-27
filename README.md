# Crawler

## 마켓브릿지 프로젝트 테스트 데이터 크롤러입니다!


# 1. scrapy 설치 
` pip install scrapy `  
` pip install bs4`


# 2. scrapy 실행
scrap_for_bridge 경로에서 `scrapy crawl <crawler 이름>`

- crawler 이름 
    - 카테고리 수집 크롤러 : coupang_cate_crawler
    - 상품 정보 수집 크롤러 : prod_detail_crawler  

# 3. output 규격

### 이미지 저장 경로
```
- 기본적으로 `../data/{ctgr1}/{ctgr2}/{ctgr3}/{product_name}/{coupang_prod_id}`  경로에 이미지가 저장된다.
    - 쿠팡 상품 번호가 기준선이다.
- 메인 썸네일 이미지는 기본경로 하위의 main_img에 저장된다.
- 상품 상세 설명 이미지는 기본경로 하위의 details에 저장된다.
- 나머지 상품 이미지들은 기본경로에 저장된다.
```

### tsv 파일 저장 데이터
```
- 기본적으로 이미지 저장시 한 row 마다 한 줄씩 생성된다.

'ctgr1' : 1뎁스 (최상위 카테고리)
'ctgr2' : 2뎁스 (중간 카테고리)
'ctgr3' : 3뎁스 (최하위 카테고리)
'product_name' : 상품명 
'img_type' : main(메인이미지), product(상품이미지), detail(상품상세이미지)
'img_seq_no' : 이미지 저장순서
'dc_rate' : 할인율
'price' : 할인 전 가격
'tags_obj' : 상품마다의 tag 정보 json 형식
'img_file_name' : 이미지 저장된 경로 + 처리된 이미지 파일 이름
```
