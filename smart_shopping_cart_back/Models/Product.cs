using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace smart_shopping_cart_back.Models;

[Table("products")]
public class Product
{
    [Key]
    [Column("product_id")]
    public long ProductId { get; set; }

    [Column("name")]
    public string Name { get; set; } = "";

    [Column("price")]
    public decimal Price { get; set; }

    [Column("category_id")]
    public string CategoryId { get; set; } = "";

    [Column("description")]
    public string? Description { get; set; }

    [Column("bay")]
    public string Bay { get; set; } = "";

    [Column("level")]
    public int Level { get; set; }

    [Column("position_index")]
    public int PositionIndex { get; set; }

    [Column("stock")]
    public int Stock { get; set; }

    [Column("active")]
    public bool Active { get; set; } = true;

    [Column("has_rfid")]
    public bool HasRfid { get; set; }

    [Column("created_at")]
    public DateTimeOffset CreatedAt { get; set; }

    [Column("updated_at")]
    public DateTimeOffset UpdatedAt { get; set; }

    // Navigation properties for EF Core relationships
    public List<ProductImage> Images { get; set; } = new();
    public List<ProductRfid> Rfids { get; set; } = new();
    public List<Review> Reviews { get; set; } = new();
}
