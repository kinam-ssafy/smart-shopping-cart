using smart_shopping_cart_back.Models;
using smart_shopping_cart_back.Repositories;

namespace smart_shopping_cart_back.Services;

/// <summary>
/// 카트 DB 서비스
/// - RFID UID로 상품 조회
/// - 카트에 상품 목록 저장
/// </summary>
public class CartDbService
{
    private readonly ILogger<CartDbService> _logger;
    private readonly IServiceScopeFactory _scopeFactory;

    public CartDbService(ILogger<CartDbService> logger, IServiceScopeFactory scopeFactory)
    {
        _logger = logger;
        _scopeFactory = scopeFactory;
    }

    /// <summary>
    /// RFID UID 배열로 상품 상세 정보 조회 (프론트엔드 DTO 형식)
    /// </summary>
    public async Task<List<ProductDto>> GetProductsByRfidUidsAsync(string[] rfidUids)
    {
        var products = new List<ProductDto>();

        if (rfidUids.Length == 0)
            return products;

        using var scope = _scopeFactory.CreateScope();
        var repository = scope.ServiceProvider.GetRequiredService<ICartRepository>();

        var productRfids = await repository.GetProductRfidsByUidsAsync(rfidUids);

        foreach (var pr in productRfids)
        {
            var p = pr.Product;
            if (p == null) continue;

            var dto = new ProductDto
            {
                Id = p.ProductId,
                Name = p.Name,
                Price = p.Price,
                Rating = p.Reviews.Any() ? (decimal)p.Reviews.Average(r => r.Rating) : 0,
                HasRfid = p.HasRfid,
                RfidUid = pr.RfidUid,
                Location = !string.IsNullOrEmpty(p.Bay) ? $"{p.Bay}-{p.Level}-{p.PositionIndex}" : null,
                Images = p.Images.OrderBy(i => i.SortOrder).Select(i => i.ImageUrl).ToList(),
                Quantity = 1,
                Detail = new ProductDetailDto
                {
                    Description = p.Description ?? "",
                    Reviews = p.Reviews.Take(5).Select(r => new ReviewDto
                    {
                        Rating = r.Rating,
                        Content = r.Content ?? "",
                        Images = !string.IsNullOrEmpty(r.ImageUrl) ? new List<string> { r.ImageUrl } : null
                    }).ToList()
                }
            };
            products.Add(dto);
        }

        return products;
    }

    /// <summary>
    /// RFID UID 배열을 받아 해당 상품 ID 목록을 반환
    /// </summary>
    public async Task<List<long>> GetProductIdsByRfidUidsAsync(string[] rfidUids)
    {
        using var scope = _scopeFactory.CreateScope();
        var repository = scope.ServiceProvider.GetRequiredService<ICartRepository>();

        var productRfids = await repository.GetProductRfidsByUidsAsync(rfidUids);
        return productRfids.Select(pr => pr.ProductId).Distinct().ToList();
    }

    /// <summary>
    /// 카트에 상품 목록 업데이트
    /// </summary>
    public async Task UpdateCartItemsAsync(int cartId, string[] rfidUids)
    {
        using var scope = _scopeFactory.CreateScope();
        var repository = scope.ServiceProvider.GetRequiredService<ICartRepository>();

        await repository.UpdateCartAsync(cartId, rfidUids);
        _logger.LogInformation($"[CartDB] 카트 {cartId} 업데이트: {rfidUids.Length}개 아이템");
    }

    /// <summary>
    /// 카트 상품 목록 조회 (RFID UID 배열)
    /// </summary>
    public async Task<string[]> GetCartItemsAsync(int cartId)
    {
        using var scope = _scopeFactory.CreateScope();
        var repository = scope.ServiceProvider.GetRequiredService<ICartRepository>();

        var cart = await repository.GetCartAsync(cartId);
        return cart?.ShoppingList ?? Array.Empty<string>();
    }

    /// <summary>
    /// 카트 상품 상세 정보 조회 (프론트엔드용)
    /// </summary>
    public async Task<List<ProductDto>> GetCartProductsAsync(int cartId)
    {
        var rfidUids = await GetCartItemsAsync(cartId);
        return await GetProductsByRfidUidsAsync(rfidUids);
    }
}
