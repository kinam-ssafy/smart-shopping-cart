using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using smart_shopping_cart_back.Data;
using smart_shopping_cart_back.Models;

namespace smart_shopping_cart_back.Services;

public static class CardQueryService
{
    public static async Task<List<ProductDto>> BuildCardsAsync(
        AppDbContext db,
        IEnumerable<long> productIds,
        CancellationToken ct = default)
    {
        var ids = productIds.Distinct().ToArray();
        if (ids.Length == 0) return new();

        var orderIndex = ids.Select((id, idx) => new { id, idx })
                            .ToDictionary(x => x.id, x => x.idx);

        // 1) Products
        var products = await db.Products
            .AsNoTracking()
            .Where(p => ids.Contains(p.ProductId))
            .Select(p => new
            {
                p.ProductId, p.Name, p.Price,
                p.Bay, p.Level, p.PositionIndex,
                p.Stock, p.Active, p.HasRfid,
                p.Description
            })
            .ToListAsync(ct);

        // 2) Images
        var images = await db.ProductImages
            .AsNoTracking()
            .Where(i => ids.Contains(i.ProductId))
            .OrderBy(i => i.ProductId)
            .ThenBy(i => i.SortOrder)
            .Select(i => new
            {
                i.ProductId,
                i.ImageUrl
            })
            .ToListAsync(ct);

        var imagesByProduct = images
            .GroupBy(x => x.ProductId)
            .ToDictionary(
                g => g.Key,
                g => g.Select(x => x.ImageUrl).ToList()
            );

        // 3) Avg rating
        var ratingStats = await db.Reviews
            .AsNoTracking()
            .Where(r => ids.Contains(r.ProductId))
            .GroupBy(r => r.ProductId)
            .Select(g => new
            {
                ProductId = g.Key,
                Avg = g.Average(x => (double)x.Rating)
            })
            .ToListAsync(ct);

        var avgByProduct = ratingStats.ToDictionary(x => x.ProductId, x => x.Avg);

        // 4) Latest reviews
        var reviews = await db.Reviews
            .AsNoTracking()
            .Where(r => ids.Contains(r.ProductId))
            .OrderByDescending(r => r.CreatedAt)
            .Select(r => new
            {
                r.ProductId,
                Dto = new ReviewDto
                {
                    Rating = r.Rating,
                    Content = r.Content ?? "",
                    Images = string.IsNullOrEmpty(r.ImageUrl) ? new List<string>() : new List<string> { r.ImageUrl }
                }
            })
            .ToListAsync(ct);

        // Cap to 3 per product
        var reviewsByProduct = reviews
            .GroupBy(x => x.ProductId)
            .ToDictionary(
                g => g.Key,
                g => g.Select(x => x.Dto).Take(3).ToList()
            );

        // Assemble
        return products
            .OrderBy(p => orderIndex.TryGetValue(p.ProductId, out var idx) ? idx : int.MaxValue)
            .Select(p => new ProductDto
            {
                Id = p.ProductId,
                Name = p.Name,
                Price = p.Price,
                Images = imagesByProduct.TryGetValue(p.ProductId, out var imgs) ? imgs : new(),
                Quantity = 1,
                Rating = (decimal)(avgByProduct.TryGetValue(p.ProductId, out var avg) ? avg : 0.0),
                Location = $"{p.Bay}-{p.Level}-{p.PositionIndex}",
                HasRfid = p.HasRfid,
                RfidUid = null,
                Detail = new ProductDetailDto
                {
                    Description = p.Description ?? "",
                    Reviews = reviewsByProduct.TryGetValue(p.ProductId, out var revs) ? revs : new()
                }
            })
            .ToList();
    }
}
