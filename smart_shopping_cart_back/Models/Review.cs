using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace smart_shopping_cart_back.Models;

[Table("reviews")]
public class Review
{
    [Key]
    [Column("review_id")]
    public Guid ReviewId { get; set; }

    [Column("product_id")]
    public long ProductId { get; set; }

    [Column("image_url")]
    public string ImageUrl { get; set; } = "";

    [Column("image_alt_text")]
    public string? ImageAltText { get; set; }

    [Column("rating")]
    public int Rating { get; set; }

    [Column("content")]
    public string? Content { get; set; }

    [Column("created_at")]
    public DateTimeOffset CreatedAt { get; set; }

    // Navigation property
    [ForeignKey("ProductId")]
    public Product? Product { get; set; }
}
