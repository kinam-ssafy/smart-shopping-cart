using smart_shopping_cart_back.Data;
using smart_shopping_cart_back.DTOs;
using smart_shopping_cart_back.Models;


namespace smart_shopping_cart_back.Services;

app.MapGet("/search", async (AppDbContext db, string query, CancellationToken ct) =>
{
    if (string.IsNullOrWhiteSpace(query))
        return Results.BadRequest(new { error = "query is required" });

    var ids = await db.Products
        .AsNoTracking()
        .Where(p => p.Active)
        .Where(p => EF.Functions.ILike(p.Name, $"%{query}%"))
        .OrderBy(p => p.Name)
        .Select(p => p.ProductId)
        .Take(100)
        .ToListAsync(ct);

    var cards = await BuildCardsAsync(db, ids, ct);
    return Results.Ok(cards);
});

app.MapGet("/search_default", async (AppDbContext db, CancellationToken ct) =>
{
    var popularIds = await db.Products
        .AsNoTracking()
        .Where(p => p.Active)
        .Select(p => new
        {
            p.ProductId,
            Avg = db.Reviews.Where(r => r.ProductId == p.ProductId)
                .Select(r => (double?)r.Rating)
                .Average() ?? 0.0,
            Cnt = db.Reviews.Count(r => r.ProductId == p.ProductId)
        })
        .OrderByDescending(x => x.Avg)
        .ThenByDescending(x => x.Cnt)
        .ThenBy(x => x.ProductId)
        .Take(6)
        .Select(x => x.ProductId)
        .ToListAsync(ct);

    var recommendedIds = await db.Products
        .AsNoTracking()
        .Where(p => p.Active)
        .OrderByDescending(p => p.CreatedAt)
        .Take(6)
        .Select(p => p.ProductId)
        .ToListAsync(ct);

    var popular = await BuildCardsAsync(db, popularIds, ct);
    var recommended = await BuildCardsAsync(db, recommendedIds, ct);

    return Results.Ok(new { popular, recommended });
});