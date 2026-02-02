using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using Pgvector;

namespace smart_shopping_cart_back.Models;

[Table("rag_chunks")]
public class RagChunk
{
    [Key]
    [Column("chunk_id")]
    public Guid ChunkId { get; set; } = Guid.NewGuid();

    [Column("product_id")]
    [ForeignKey("Product")]
    public long ProductId { get; set; }

    public virtual Product Product { get; set; }

    [Column("source_type")]
    public string SourceType { get; set; } = "description";

    [Column("chunk_index")]
    public int ChunkIndex { get; set; }

    [Column("chunk_text")]
    public string ChunkText { get; set; }

    [Column("embedding", TypeName = "vector(1536)")]
    public Vector Embedding { get; set; } = default!;

    [Column("metadata", TypeName = "jsonb")]
    public string Metadata { get; set; } = "{}";

    [Column("created_at")]
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
}
