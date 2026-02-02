using smart_shopping_cart_back.Models;

namespace smart_shopping_cart_back.Repositories;

public interface ICartRepository
{
    Task<List<ProductRfid>> GetProductRfidsByUidsAsync(string[] rfidUids);
    Task<Product?> GetProductByIdAsync(long productId);
    Task<Cart?> GetCartAsync(int cartId);
    Task UpdateCartAsync(int cartId, string[] rfidUids);
    Task<Cart?> GetActiveCartAsync(CancellationToken ct);
    Task<List<long>> GetProductIdsAsync(long cartId, CancellationToken ct);
}
