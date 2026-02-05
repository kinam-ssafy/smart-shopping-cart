using Microsoft.EntityFrameworkCore;
using smart_shopping_cart_back.Data;
using smart_shopping_cart_back.Models;

namespace smart_shopping_cart_back.Repositories;

public class CartRepository : ICartRepository
{
    private readonly AppDbContext _context;

    public CartRepository(AppDbContext context)
    {
        _context = context;
    }

    public async Task<List<ProductRfid>> GetProductRfidsByUidsAsync(string[] rfidUids)
    {
        if (rfidUids.Length == 0)
            return new List<ProductRfid>();

        return await _context.ProductRfids
            .Include(pr => pr.Product)
                .ThenInclude(p => p.Images)
            .Include(pr => pr.Product)
                .ThenInclude(p => p.Reviews)
            .Where(pr => rfidUids.Contains(pr.RfidUid))
            .ToListAsync();
    }

    public async Task<Product?> GetProductByIdAsync(long productId)
    {
        return await _context.Products
            .AsNoTracking()
            .Include(p => p.Images)
            .Include(p => p.Reviews)
            .FirstOrDefaultAsync(p => p.ProductId == productId);
    }

    public async Task<Cart?> GetCartAsync(int cartId)
    {
        return await _context.Carts.FirstOrDefaultAsync(c => c.CartId == cartId);
    }

    public async Task UpdateCartAsync(int cartId, string[] rfidUids)
    {
        var cart = await _context.Carts.FindAsync(cartId);
        
        if (cart == null)
        {
            cart = new Cart 
            { 
                CartId = cartId, 
                Status = "active", 
                ShoppingList = rfidUids,
                CreatedAt = DateTime.UtcNow,
                UpdatedAt = DateTime.UtcNow
            };
            _context.Carts.Add(cart);
        }
        else
        {
            cart.ShoppingList = rfidUids;
            cart.UpdatedAt = DateTime.UtcNow;
            _context.Carts.Update(cart);
        }

        await _context.SaveChangesAsync();
    }
    public async Task<Cart?> GetActiveCartAsync(CancellationToken ct)
    {
        return await _context.Carts
            .AsNoTracking()
            .Where(c => c.Status == "active")
            .OrderByDescending(c => c.UpdatedAt)
            // Use ct for async cancellation
            .FirstOrDefaultAsync(ct);
    }

    public async Task<List<long>> GetProductIdsAsync(long cartId, CancellationToken ct)
    {
        var shoppingList = await _context.Carts
            .AsNoTracking()
            .Where(c => c.CartId == cartId && c.Status == "active")
            .Select(c => c.ShoppingList)
            .FirstOrDefaultAsync(ct);

        if (shoppingList == null || shoppingList.Length == 0)
            return new List<long>();

        return await _context.ProductRfids
            .AsNoTracking()
            .Where(pr => shoppingList.Contains(pr.RfidUid))
            .Select(pr => pr.ProductId)
            .ToListAsync(ct);
    }
}
