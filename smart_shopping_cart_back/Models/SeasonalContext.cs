using Pgvector;

namespace smart_shopping_cart_back.Models;

public class SeasonalContext
{
    public string Season { get; set; } = null!;
    public string ContextText { get; set; } = null!;
    public Vector Embedding { get; set; } = null!;
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
}
