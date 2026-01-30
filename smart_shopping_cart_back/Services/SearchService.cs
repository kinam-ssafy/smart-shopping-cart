using Microsoft.EntityFrameworkCore;
using smart_shopping_cart_back.Data;
using smart_shopping_cart_back.Models;
using smart_shopping_cart_back.Services;

namespace smart_shopping_cart_back.Services;

public class SearchService : ISearchService
{
    private readonly AppDbContext _db;

    // Dependency Injection: Requesting the Database
    public SearchService(AppDbContext db)
    {
        _db = db;
    }

    public async Task<List<CardTemplateDto>> SearchByNameAsync(string query, CancellationToken ct)
    {
        // Simple search example
        var ids = await _db.Products
            .AsNoTracking()
            .Where(p => p.Active && EF.Functions.ILike(p.Name, $"%{query}%"))
            .Select(p => p.ProductId)
            .ToListAsync(ct);

        return await CardQueryService.BuildCardsAsync(_db, ids, ct);
    }

    public async Task<SearchDefaultResponseDto> SearchDefaultAsync(CancellationToken ct)
    {
        // 1. LINQ: Find Popular Products
        var popularIds = await _db.Products
            .AsNoTracking()
            .Where(p => p.Active)
            .Select(p => new
            {
                p.ProductId,
                // Calculate Average Rating
                Avg = _db.Reviews.Where(r => r.ProductId == p.ProductId)
                    .Select(r => (double?)r.Rating)
                    .Average() ?? 0.0,
                // Calculate Review Count
                Cnt = _db.Reviews.Count(r => r.ProductId == p.ProductId)
            })
            .OrderByDescending(x => x.Avg) // Sort by Rating
            .ThenByDescending(x => x.Cnt)  // Then by Count
            .ThenBy(x => x.ProductId)
            .Take(6)
            .Select(x => x.ProductId)
            .ToListAsync(ct);

        var recommendedIds = await _db.Products
            .AsNoTracking()
            .Where(p => p.Active)
            .OrderByDescending(p => p.CreatedAt)
            .Take(6)
            .Select(p => p.ProductId)
            .ToListAsync(ct);

        var popular = await CardQueryService.BuildCardsAsync(_db, popularIds, ct);
        var recommended = await CardQueryService.BuildCardsAsync(_db, recommendedIds, ct);

        return new SearchDefaultResponseDto(popular, recommended);
    }
}
