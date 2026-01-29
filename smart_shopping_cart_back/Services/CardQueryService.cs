using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using smart_shopping_cart_back.Data;
using smart_shopping_cart_back.DTOs;

namespace smart_shopping_cart_back.Services;

public static class CardQueryService
{
    public static async Task<List<CardTemplateDto>> BuildCardsAsync(
        AppDbContext db,
        IEnumerable<string> productIds,
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
                p.ProductId, p.Name, p.Price, p.Bay, p.Level, p.PositionIndex,
                p.Stock, p.Active,
                LocationText = (string?)null
            })
            .ToListAsync(ct);

        // 2) Images (optionally cap per product in memory)
        var images = await db.ProductImages
            .AsNoTracking()
            .Where(i => ids.Contains(i.ProductId))
            .OrderBy(i => i.ProductId)
            .ThenBy(i => i.SortOrder)
            .Select(i => new
            {
                i.ProductId,
                Dto = new ProductImageForCardDto(
                    i.ProductImageId, i.ImageUrl, i.ImageAltText, i.SortOrder
                )
            })
            .ToListAsync(ct);

        var imagesByProduct = images
            .GroupBy(x => x.ProductId)
            .ToDictionary(
                g => g.Key,
                g => g.Select(x => x.Dto).ToList()
            );

        // 3) Avg rating + count in DB (small result)
        var ratingStats = await db.Reviews
            .AsNoTracking()
            .Where(r => ids.Contains(r.ProductId))
            .GroupBy(r => r.ProductId)
            .Select(g => new
            {
                ProductId = g.Key,
                Avg = g.Average(x => (double)x.Rating),
                Count = g.Count()
            })
            .ToListAsync(ct);

        var avgByProduct = ratingStats.ToDictionary(x => x.ProductId, x => x.Avg);

        // 4) Latest reviews (cap per product in memory)
        var reviews = await db.Reviews
            .AsNoTracking()
            .Where(r => ids.Contains(r.ProductId))
            .OrderByDescending(r => r.CreatedAt)
            .Select(r => new
            {
                r.ProductId,
                Dto = new ReviewForCardDto(
                    r.ReviewId, r.ImageUrl, r.ImageAltText, r.Rating, r.Content, r.CreatedAt
                )
            })
            .ToListAsync(ct);

        // Cap to 3 per product (feed-friendly)
        var reviewsByProduct = reviews
            .GroupBy(x => x.ProductId)
            .ToDictionary(
                g => g.Key,
                g => g.Select(x => x.Dto).Take(3).ToList()
            );

        // Assemble
        return products
            .OrderBy(p => orderIndex.TryGetValue(p.ProductId, out var idx) ? idx : int.MaxValue)
            .Select(p => new CardTemplateDto(
                p.ProductId, p.Name, p.Price, p.LocationText,
                p.Bay, p.Level, p.PositionIndex, p.Stock, p.Active,
                avgByProduct.TryGetValue(p.ProductId, out var avg) ? avg : 0.0,
                imagesByProduct.TryGetValue(p.ProductId, out var imgs) ? imgs : new(),
                reviewsByProduct.TryGetValue(p.ProductId, out var revs) ? revs : new()
            ))
            .ToList();
    }
}
