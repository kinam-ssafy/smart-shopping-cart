using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace smart_shopping_cart_back.Models;

[Table("product_images")]
public class ProductImage
{
    [Key]
    [Column("product_image_id")]
    public Guid ProductImageId { get; set; }

    [Column("product_id")]
    public string ProductId { get; set; } = null!;

    [Column("image_url")]
    public string ImageUrl { get; set; } = "";

    [Column("image_alt_text")]
    public string? ImageAltText { get; set; }

    [Column("sort_order")]
    public int SortOrder { get; set; }

    [Column("created_at")]
    public DateTimeOffset CreatedAt { get; set; }
}
