using Pgvector;

public interface IRecommendationRepository
{
    Task<List<long>> FindRecommendedProductIdsAsync(
        Vector queryVector,
        IReadOnlyCollection<long> excludeProductIds,
        int topK,
        CancellationToken ct
    );
}
