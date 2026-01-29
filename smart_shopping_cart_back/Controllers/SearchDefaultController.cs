using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

namespace smart_shopping_cart_back.Controllers;

[ApiController]
[Route("")]
public class SearchController : ControllerBase
{
    private readonly AppDbContext _db;

    public SearchController(AppDbContext db)
    {
        _db = db;
    }

    // GET /search_default
    [HttpGet("search_default")]
    public async Task<ActionResult<SearchDefaultResponseDto>> SearchDefault(CancellationToken ct)
    {
        var popularIds = await _db.Products
            .AsNoTracking()
            .Where(p => p.Active)
            .Select(p => new
            {
                p.ProductId,
                Avg = _db.Reviews.Where(r => r.ProductId == p.ProductId)
                    .Select(r => (double?)r.Rating)
                    .Average() ?? 0.0,
                Cnt = _db.Reviews.Count(r => r.ProductId == p.ProductId)
            })
            .OrderByDescending(x => x.Avg)
            .ThenByDescending(x => x.Cnt)
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

        return Ok(new SearchDefaultResponseDto(popular, recommended));
    }
    private static Task<List<CardTemplateDto>> BuildCardsAsync(
        AppDbContext db,
        IEnumerable<string> productIds,
        CancellationToken ct = default)
        => CardQueryService.BuildCardsAsync(db, productIds, ct); 
}
