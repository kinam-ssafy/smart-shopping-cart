-- 상품 이미지 데이터 (Unsplash 무료 이미지 URL 사용)
-- 03_products.sql 실행 후 실행

INSERT INTO product_images (product_id, image_url, image_alt_text, sort_order) VALUES
-- 과일 (1-15)
(1, 'https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=400', '청송 꿀사과', 0),
(2, 'https://images.unsplash.com/photo-1568702846914-96b305d2aaeb?w=400', '청송 부사 사과', 0),
(3, 'https://images.unsplash.com/photo-1611080626919-7cf5a9dbab5b?w=400', '제주 감귤', 0),
(4, 'https://images.unsplash.com/photo-1514756331096-242fdeb70d4a?w=400', '고당도 배', 0),
(5, 'https://images.unsplash.com/photo-1537640538966-79f369143f8f?w=400', '샤인머스캣', 0),
(6, 'https://images.unsplash.com/photo-1423483641154-5411ec9c0ddf?w=400', '캠벨 포도', 0),
(7, 'https://images.unsplash.com/photo-1571575173700-afb9492e6a50?w=400', '성주 참외', 0),
(8, 'https://images.unsplash.com/photo-1464965911861-746a04b4bca6?w=400', '딸기', 0),
(9, 'https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=400', '바나나', 0),
(10, 'https://images.unsplash.com/photo-1553279768-865429fa0078?w=400', '망고', 0),
(11, 'https://images.unsplash.com/photo-1550258987-190a2d41a8ba?w=400', '파인애플', 0),
(12, 'https://images.unsplash.com/photo-1585059895524-72359e06133a?w=400', '키위', 0),
(13, 'https://images.unsplash.com/photo-1625437093228-7a3e75b2cae6?w=400', '건포도', 0),
(14, 'https://images.unsplash.com/photo-1587049352847-81eacd3a0622?w=400', '건망고', 0),

-- 채소 (15-28) - ID 수정
(15, 'https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=400', '시금치', 0),
(16, 'https://images.unsplash.com/photo-1622206151226-18ca2c9ab4a1?w=400', '로메인 상추', 0),
(17, 'https://images.unsplash.com/photo-1540420773420-3366772f4999?w=400', '청경채', 0),
(18, 'https://images.unsplash.com/photo-1594282486552-05b4d80fbb9f?w=400', '양배추', 0),
(19, 'https://images.unsplash.com/photo-1598170845058-32b9d6a5da37?w=400', '당근', 0),
(20, 'https://images.unsplash.com/photo-1518977676601-b53f82aja137?w=400', '감자', 0),
(21, 'https://images.unsplash.com/photo-1596097557994-49dff5c48a77?w=400', '고구마', 0),
(22, 'https://images.unsplash.com/photo-1618512496248-a07fe83aa8cb?w=400', '양파', 0),
(23, 'https://images.unsplash.com/photo-1540148426945-6cf22a6b2383?w=400', '마늘', 0),
(24, 'https://images.unsplash.com/photo-1504545102780-26774c1bb073?w=400', '새송이버섯', 0),
(25, 'https://images.unsplash.com/photo-1552825898-86d0de39c4e4?w=400', '표고버섯', 0),
(26, 'https://images.unsplash.com/photo-1504545102780-26774c1bb073?w=400', '팽이버섯', 0),

-- 유제품 (27-37) - ID 수정 (31에서 27로)
(27, 'https://images.unsplash.com/photo-1563636619-e9143da7973b?w=400', '우유', 0),
(28, 'https://images.unsplash.com/photo-1550583724-b2692b85b150?w=400', '저지방우유', 0),
(29, 'https://images.unsplash.com/photo-1628088062854-d1870b4553da?w=400', '초콜릿 우유', 0),
(30, 'https://images.unsplash.com/photo-1563636619-e9143da7973b?w=400', '유기농 우유', 0),
(31, 'https://images.unsplash.com/photo-1486297678162-eb2a19b0a32d?w=400', '체다 치즈', 0),
(32, 'https://images.unsplash.com/photo-1452195100486-9cc805987862?w=400', '모짜렐라 치즈', 0),
(33, 'https://images.unsplash.com/photo-1559561853-08451507cbe7?w=400', '까망베르 치즈', 0),
(34, 'https://images.unsplash.com/photo-1488477181946-6428a0291777?w=400', '플레인 요거트', 0),
(35, 'https://images.unsplash.com/photo-1571212515416-fef01fc43637?w=400', '그릭 요거트', 0),
(36, 'https://images.unsplash.com/photo-1505252585461-04db1eb84625?w=400', '딸기 요거트', 0),
(37, 'https://images.unsplash.com/photo-1505252585461-04db1eb84625?w=400', '블루베리 요거트', 0),

-- 육류 (38-47) - ID 수정 (46에서 38로)
(38, 'https://images.unsplash.com/photo-1603048297172-c92544798d5a?w=400', '한우 등심', 0),
(39, 'https://images.unsplash.com/photo-1588168333986-5078d3ae3976?w=400', '한우 갈비살', 0),
(40, 'https://images.unsplash.com/photo-1602473812169-7a9a27f2b2f3?w=400', '호주산 안심', 0),
(41, 'https://images.unsplash.com/photo-1602470520998-f4a52199a3d6?w=400', '삼겹살', 0),
(42, 'https://images.unsplash.com/photo-1602470520998-f4a52199a3d6?w=400', '목살', 0),
(43, 'https://images.unsplash.com/photo-1602470520998-f4a52199a3d6?w=400', '앞다리살', 0),
(44, 'https://images.unsplash.com/photo-1604503468506-a8da13d82791?w=400', '닭가슴살', 0),
(45, 'https://images.unsplash.com/photo-1598103442097-8b74394b95c6?w=400', '닭다리살', 0),
(46, 'https://images.unsplash.com/photo-1598103442097-8b74394b95c6?w=400', '닭볶음탕용', 0),
(47, 'https://images.unsplash.com/photo-1580651315530-69c8e0026377?w=400', '훈제오리', 0),

-- 수산물 (48-57) - ID 수정 (56에서 48로)
(48, 'https://images.unsplash.com/photo-1574781330855-d0db8cc6a79c?w=400', '생연어', 0),
(49, 'https://images.unsplash.com/photo-1510130387422-82bed34b37e9?w=400', '고등어', 0),
(50, 'https://images.unsplash.com/photo-1519708227418-c8fd9a32b7a2?w=400', '갈치', 0),
(51, 'https://images.unsplash.com/photo-1579631542720-3a87824fff86?w=400', '광어 회', 0),
(52, 'https://images.unsplash.com/photo-1565680018434-b513d5e5fd47?w=400', '새우', 0),
(53, 'https://images.unsplash.com/photo-1590759668628-05b0fc34bb70?w=400', '홍합', 0),
(54, 'https://images.unsplash.com/photo-1590759668628-05b0fc34bb70?w=400', '바지락', 0),
(55, 'https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=400', '오징어', 0),
(56, 'https://images.unsplash.com/photo-1565680018434-b513d5e5fd47?w=400', '낙지', 0),
(57, 'https://images.unsplash.com/photo-1623855244183-52fd8d3ce2f7?w=400', '전복', 0),

-- 음료 (58-68) - ID 수정 (66에서 58로)
(58, 'https://images.unsplash.com/photo-1548839140-29a749e1cf4d?w=400', '삼다수', 0),
(59, 'https://images.unsplash.com/photo-1564419320461-6870880221ad?w=400', '에비앙', 0),
(60, 'https://images.unsplash.com/photo-1527960471264-932f39eb5846?w=400', '페리에', 0),
(61, 'https://images.unsplash.com/photo-1621506289937-a8e4df240d0b?w=400', '오렌지 주스', 0),
(62, 'https://images.unsplash.com/photo-1576673442511-7e39b6545c87?w=400', '사과 주스', 0),
(63, 'https://images.unsplash.com/photo-1559181567-c3190ca9959b?w=400', '토마토 주스', 0),
(64, 'https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=400', '커피', 0),
(65, 'https://images.unsplash.com/photo-1556881286-fc6915169721?w=400', '녹차', 0),
(66, 'https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=400', '캐모마일 차', 0),
(67, 'https://images.unsplash.com/photo-1563227812-0ea4c22e6cc8?w=400', '콤부차', 0),

-- 과자/스낵 (68-77) - ID 수정 (76에서 68로)
(68, 'https://images.unsplash.com/photo-1566478989037-eec170784d0b?w=400', '포카칩', 0),
(69, 'https://images.unsplash.com/photo-1621447504864-d8686e12698c?w=400', '프링글스', 0),
(70, 'https://images.unsplash.com/photo-1599490659213-e2b9527bd087?w=400', '꼬깔콘', 0),
(71, 'https://images.unsplash.com/photo-1582058091505-f87a2e55a40f?w=400', '하리보', 0),
(72, 'https://images.unsplash.com/photo-1571997478779-2adcbbe9ab2f?w=400', '껌', 0),
(73, 'https://images.unsplash.com/photo-1582058091505-f87a2e55a40f?w=400', '마이쮸', 0),
(74, 'https://images.unsplash.com/photo-1549007994-cb92caebd54b?w=400', '초콜릿', 0),
(75, 'https://images.unsplash.com/photo-1548907040-4baa42d10919?w=400', '페레로 로쉐', 0),
(76, 'https://images.unsplash.com/photo-1527904324834-3bda86da6771?w=400', '킷캣', 0),
(77, 'https://images.unsplash.com/photo-1558961363-fa8fdf82db35?w=400', '오레오', 0),

-- 냉동식품 (78-84) - ID 수정 (86에서 78로)
(78, 'https://images.unsplash.com/photo-1496116218417-1a781b1c416c?w=400', '만두', 0),
(79, 'https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=400', '냉동 라면', 0),
(80, 'https://images.unsplash.com/photo-1512058564366-18510be2db19?w=400', '볶음밥', 0),
(81, 'https://images.unsplash.com/photo-1497034825429-c343d7c6a68f?w=400', '하겐다즈', 0),
(82, 'https://images.unsplash.com/photo-1488900128323-21503983a07e?w=400', '메로나', 0),
(83, 'https://images.unsplash.com/photo-1570197788417-0e82375c9371?w=400', '월드콘', 0),
(84, 'https://images.unsplash.com/photo-1497034825429-c343d7c6a68f?w=400', '인절미 아이스', 0),

-- 베이커리 (85-89) - ID 수정 (93에서 85로)
(85, 'https://images.unsplash.com/photo-1509440159596-0249088772ff?w=400', '식빵', 0),
(86, 'https://images.unsplash.com/photo-1555507036-ab1f4038808a?w=400', '크로와상', 0),
(87, 'https://images.unsplash.com/photo-1549931319-a545dcf3bc73?w=400', '바게트', 0),
(88, 'https://images.unsplash.com/photo-1565958011703-44f9829ba187?w=400', '딸기 케이크', 0),
(89, 'https://images.unsplash.com/photo-1571877227200-a0d98ea607e9?w=400', '티라미수', 0),

-- 생활용품 (90-92) - ID 수정 (98에서 90으로)
(90, 'https://images.unsplash.com/photo-1583947215259-38e31be8751f?w=400', '화장지', 0),
(91, 'https://images.unsplash.com/photo-1582735689369-4fe89db7114c?w=400', '세탁세제', 0),
(92, 'https://images.unsplash.com/photo-1582735689369-4fe89db7114c?w=400', '퍼실 세제', 0)
ON CONFLICT DO NOTHING;
