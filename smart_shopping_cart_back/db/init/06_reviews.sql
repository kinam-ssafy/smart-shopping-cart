-- 리뷰 데이터 (RFID 등록 상품용 목데이터)
-- 05_product_images.sql 실행 후 실행

-- RFID 등록 상품: 1(청송 꿀사과), 2(청송 부사 사과), 3(제주 감귤), 9(바나나)
--                 27(서울우유), 28(저지방우유), 44(닭가슴살), 68(포카칩)

INSERT INTO reviews (product_id, image_url, image_alt_text, rating, content) VALUES
-- 청송 꿀사과 (product_id: 1)
(1, 'https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=200', '사과 리뷰', 5, '정말 달고 맛있어요! 아이들이 너무 좋아해서 또 주문했습니다.'),
(1, 'https://images.unsplash.com/photo-1568702846914-96b305d2aaeb?w=200', '사과 리뷰', 4, '신선하고 아삭아삭해요. 다만 크기가 조금 작았어요.'),
(1, 'https://images.unsplash.com/photo-1579613832125-5d34a13ffe2a?w=200', '사과 리뷰', 5, '꿀처럼 달아요! 청송 사과 최고입니다.'),

-- 청송 부사 사과 (product_id: 2)
(2, 'https://images.unsplash.com/photo-1568702846914-96b305d2aaeb?w=200', '부사 사과 리뷰', 5, '과즙이 풍부하고 새콤달콤해요!'),
(2, 'https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6?w=200', '부사 사과 리뷰', 4, '아침마다 먹으니 기분이 좋아져요.'),

-- 제주 감귤 (product_id: 3)
(3, 'https://images.unsplash.com/photo-1611080626919-7cf5a9dbab5b?w=200', '감귤 리뷰', 5, '제주 감귤 특유의 상큼함! 껍질도 얇아서 먹기 편해요.'),
(3, 'https://images.unsplash.com/photo-1582979512210-99b6a53386f9?w=200', '감귤 리뷰', 5, '비타민C 충전! 겨울철 필수템입니다.'),
(3, 'https://images.unsplash.com/photo-1547514701-42782101795e?w=200', '감귤 리뷰', 4, '대체로 맛있는데 가끔 신 것도 있어요.'),

-- 바나나 (product_id: 9)
(9, 'https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?w=200', '바나나 리뷰', 5, '운동 전에 먹기 딱 좋아요! 에너지 충전됩니다.'),
(9, 'https://images.unsplash.com/photo-1603833665858-e61d17a86224?w=200', '바나나 리뷰', 4, '아이 이유식에 넣어주니 잘 먹어요.'),

-- 서울우유 1L (product_id: 27)
(27, 'https://images.unsplash.com/photo-1563636619-e9143da7973b?w=200', '우유 리뷰', 5, '매일 아침 시리얼에 넣어 먹어요. 신선해요!'),
(27, 'https://images.unsplash.com/photo-1550583724-b2692b85b150?w=200', '우유 리뷰', 4, '1등급 원유라 그런지 고소합니다.'),
(27, 'https://images.unsplash.com/photo-1563636619-e9143da7973b?w=200', '우유 리뷰', 5, '아이들 칼슘 보충에 좋아요!'),

-- 매일 저지방우유 (product_id: 28)
(28, 'https://images.unsplash.com/photo-1550583724-b2692b85b150?w=200', '저지방 우유 리뷰', 4, '다이어트 중인데 부담 없이 마실 수 있어요.'),
(28, 'https://images.unsplash.com/photo-1563636619-e9143da7973b?w=200', '저지방 우유 리뷰', 4, '맛은 일반 우유보다 조금 가벼워요.'),

-- 닭가슴살 (product_id: 44)
(44, 'https://images.unsplash.com/photo-1604503468506-a8da13d82791?w=200', '닭가슴살 리뷰', 5, '헬스 후 단백질 보충에 최고! 부드럽고 맛있어요.'),
(44, 'https://images.unsplash.com/photo-1598103442097-8b74394b95c6?w=200', '닭가슴살 리뷰', 5, '에어프라이어에 구우면 정말 맛있어요.'),
(44, 'https://images.unsplash.com/photo-1604503468506-a8da13d82791?w=200', '닭가슴살 리뷰', 4, '샐러드에 넣으니 든든한 한 끼가 됩니다.'),

-- 포카칩 (product_id: 68)
(68, 'https://images.unsplash.com/photo-1566478989037-eec170784d0b?w=200', '포카칩 리뷰', 5, '바삭바삭! 영화 볼 때 필수 간식이에요.'),
(68, 'https://images.unsplash.com/photo-1621447504864-d8686e12698c?w=200', '포카칩 리뷰', 4, '맥주 안주로 최고입니다.'),
(68, 'https://images.unsplash.com/photo-1566478989037-eec170784d0b?w=200', '포카칩 리뷰', 5, '중독성 있는 맛! 한 봉지 금방 비워요.')
ON CONFLICT DO NOTHING;
