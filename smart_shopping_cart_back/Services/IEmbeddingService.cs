using Pgvector;

public interface IEmbeddingService
{
    Task<Vector> EmbedAsync(string text, CancellationToken ct);
}
