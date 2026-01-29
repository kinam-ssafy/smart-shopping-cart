using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace smart_shopping_cart_back.Models;

[Table("products")]
public class Product
{
    [Key]
    [Column("product_id")]
    public string ProductId { get; set; } = null!;

    [Column("name")]
    public string Name { get; set; } = "";

    [Column("price")]
    public decimal Price { get; set; }

    [Column("category_id")]
    public int CategoryId { get; set; }

    [Column("bay")]
    public string Bay { get; set; } = "";

    [Column("level")]
    public int Level { get; set; }

    [Column("position_index")]
    public int PositionIndex { get; set; }

    [Column("stock")]
    public int Stock { get; set; }

    [Column("active")]
    public bool Active { get; set; }

    [Column("created_at")]
    public DateTimeOffset CreatedAt { get; set; }

    [Column("updated_at")]
    public DateTimeOffset UpdatedAt { get; set; }
}
