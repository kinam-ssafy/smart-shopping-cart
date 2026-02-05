using Microsoft.EntityFrameworkCore;
using Npgsql;
using Pgvector;
using smart_shopping_cart_back.Data;

namespace smart_shopping_cart_back.Repositories;

public class SeasonalContextRepository : ISeasonalContextRepository
{
    private readonly AppDbContext _db;

    public SeasonalContextRepository(AppDbContext db)
    {
        _db = db;
    }

    public async Task<Vector?> GetSeasonalEmbeddingAsync(string season, CancellationToken ct)
    {
        var seasonalContext = await _db.SeasonalContexts
            .AsNoTracking()
            .Where(x => x.Season == season)
            .FirstOrDefaultAsync(ct);

        return seasonalContext?.Embedding;
    }
}

public sealed class ScalarVector
{
    public Vector Value { get; set; } = null!;
}
