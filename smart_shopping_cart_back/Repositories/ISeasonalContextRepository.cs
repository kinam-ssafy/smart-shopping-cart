using Pgvector;

namespace smart_shopping_cart_back.Repositories;

public interface ISeasonalContextRepository
{
    Task<Vector?> GetSeasonalEmbeddingAsync(string season, CancellationToken ct);
}
