using Microsoft.EntityFrameworkCore;
using Npgsql;
using Pgvector;
using smart_shopping_cart_back.Data;

public class RecommendationRepository : IRecommendationRepository
{
    private readonly AppDbContext _db;

    public RecommendationRepository(AppDbContext db)
    {
        _db = db;
    }

    public async Task<List<long>> FindRecommendedProductIdsAsync(
        Vector queryVector,
        IReadOnlyCollection<long> excludeProductIds,
        int topK,
        CancellationToken ct)
    {
        var sql = @"
            SELECT rc.product_id AS value
            FROM rag_chunks rc
            JOIN products p ON p.product_id = rc.product_id
            WHERE rc.source_type = 'description'
              AND rc.chunk_index = 0
              AND p.active = true
              AND p.stock > 0
              AND NOT (rc.product_id = ANY(@exclude_ids))
            ORDER BY rc.embedding <=> @query_vec
            LIMIT @top_k;
        ";

        var parameters = new[]
        {
            new NpgsqlParameter<long[]>("exclude_ids", excludeProductIds.ToArray()),
            new NpgsqlParameter("query_vec", queryVector),
            new NpgsqlParameter<int>("top_k", topK)
        };

        return await _db.Set<ScalarLong>()
            .FromSqlRaw(sql, parameters)
            .AsNoTracking()
            .Select(x => x.Value)
            .ToListAsync(ct);
    }
}

public sealed class ScalarLong
{
    public long Value { get; set; }
}
