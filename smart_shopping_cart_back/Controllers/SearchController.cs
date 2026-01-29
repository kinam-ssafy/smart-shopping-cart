using Microsoft.AspNetCore.Mvc;
using smart_shopping_cart_back.Services;
using Microsoft.EntityFrameworkCore;
using smart_shopping_cart_back.Data;

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

    [HttpGet("search")]
    public async Task<IActionResult> Search(
        [FromQuery] string query,
        CancellationToken ct
        )
    {
        if (string.IsNullOrWhiteSpace(query))
            return BadRequest(new { error = "query is required" });

        query = query.Trim();

        var ids = await _db.Products
            .AsNoTracking()
            .Where(p => p.Active)
            .Where(p => EF.Functions.ILike(p.Name, $"%{query}%"))
            .OrderBy(p => p.Name)
            .Select(p => p.ProductId)
            .Take(100)
            .ToListAsync(ct);

        var cards = await CardQueryService.BuildCardsAsync(_db, ids, ct);
        return Ok(cards);
    }
}