namespace smart_shopping_cart_back.Models;

/// <summary>
/// 통합 상품 DTO (카트/검색 공용)
/// </summary>
public class ProductDto
{
    public long Id { get; set; }
    public string Name { get; set; } = "";
    public decimal Price { get; set; }
    public List<string> Images { get; set; } = new();      // 이미지 URL 배열
    public int Quantity { get; set; } = 1;                 // 카트용 (검색에서는 1)
    public decimal Rating { get; set; }                    // 평균 평점
    public string? Location { get; set; }                  // "A-2-1" 형식
    public bool HasRfid { get; set; }
    public string? RfidUid { get; set; }                   // 카트용 (검색에서는 null)
    public ProductDetailDto? Detail { get; set; }          // 확장 상세 정보
}

public class ProductDetailDto
{
    public string Description { get; set; } = "";
    public List<ReviewDto> Reviews { get; set; } = new();
}

public class ReviewDto
{
    public decimal Rating { get; set; }
    public string Content { get; set; } = "";
    public List<string>? Images { get; set; }
}

/// <summary>
/// Search 기본 화면 응답
/// </summary>
public record SearchDefaultResponseDto(
    List<ProductDto> Popular,
    List<ProductDto> Recommended
);
