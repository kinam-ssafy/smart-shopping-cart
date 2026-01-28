using smart_shopping_cart_back.Data;
using smart_shopping_cart_back.DTOs;

namespace smart_shopping_cart_back.Models;

static async Task<List<CardTemplateDto>> BuildCardsAsync(
    AppDbContext db,
    IEnumerable<string> productIds,
    CancellationToken ct = default)
{
    var ids = productIds.Distinct().ToArray();
    if (ids.Length == 0) return new();

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

    var images = await db.ProductImages
        .AsNoTracking()
        .Where(i => ids.Contains(i.ProductId))
        .OrderBy(i => i.SortOrder)
        .Select(i => new
        {
            i.ProductId,
            Dto = new ProductImageForCardDto(
                i.ProductImageId, i.ImageUrl, i.ImageAltText, i.SortOrder
            )
        })
        .ToListAsync(ct);

    var reviews = await db.Reviews
        .AsNoTracking()
        .Where(r => ids.Contains(r.ProductId))
        .OrderByDescending(r => r.CreatedAt)
        .Select(r => new
        {
            r.ProductId,
            r.Rating,
            Dto = new ReviewForCardDto(
                r.ReviewId, r.ImageUrl, r.ImageAltText, r.Rating, r.Content, r.CreatedAt
            )
        })
        .ToListAsync(ct);

    var imagesByProduct = images
        .GroupBy(x => x.ProductId)
        .ToDictionary(g => g.Key, g => g.Select(x => x.Dto).ToList());

    var reviewsByProduct = reviews
        .GroupBy(x => x.ProductId)
        .ToDictionary(g => g.Key, g => g.Select(x => x.Dto).ToList());

    var ratingStats = await db.Reviews
        .AsNoTracking()
        .Where(r => ids.Contains(r.ProductId))
        .GroupBy(r => r.ProductId)
        .Select(g => new
        {
            ProductId = g.Key,
            Avg = g.Average(r => (double)r.Rating),
            Cnt = g.Count()
        });

    var avgByProduct = ratingStats.ToDictionary(g => g.Key, g => g.Avg);

    var orderIndex = ids.Select((id, idx) => (id, idx)).ToDictionary(x => x.id, x => x.idx);

    return products
        .OrderBy(p => orderIndex[p.ProductId])
        .Select(p => new CardTemplateDto(
            p.ProductId, p.Name, p.Price, p.LocationText,
            p.Bay, p.Level, p.PositionIndex, p.Stock, p.Active,
            avgByProduct.TryGetValue(p.ProductId, out var avg) ? avg : 0.0,
            imagesByProduct.TryGetValue(p.ProductId, out var imgs) ? imgs : new(),
            reviewsByProduct.TryGetValue(p.ProductId, out var revs) ? revs : new()
        ))
        .ToList();
}