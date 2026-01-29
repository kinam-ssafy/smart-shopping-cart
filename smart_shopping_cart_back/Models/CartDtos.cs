namespace smart_shopping_cart_back.Models;

/// <summary>
/// 카트 상품 DTO (프론트엔드 전송용)
/// </summary>
public class CartProductDto
{
    public long Id { get; set; }
    public string Name { get; set; } = "";
    public decimal Price { get; set; }
    public string? Image { get; set; }
    public int Quantity { get; set; } = 1;
    public decimal Rating { get; set; }
    public string? Location { get; set; }
    public bool HasRfid { get; set; }
    public string? RfidUid { get; set; }
    public CartProductDetailDto? Detail { get; set; }
}

public class CartProductDetailDto
{
    public List<string> Images { get; set; } = new();
    public string Description { get; set; } = "";
    public decimal AverageRating { get; set; }
    public List<ReviewDto> Reviews { get; set; } = new();
}

public class ReviewDto
{
    public decimal Rating { get; set; }
    public string Content { get; set; } = "";
    public List<string>? Images { get; set; }
}
