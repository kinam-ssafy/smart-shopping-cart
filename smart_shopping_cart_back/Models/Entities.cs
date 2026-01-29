using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace smart_shopping_cart_back.Models;

[Table("products")]
public class Product
{
    [Key]
    [Column("product_id")]
    public long ProductId { get; set; }

    [Required]
    [Column("name")]
    public string Name { get; set; } = "";

    [Required]
    [Column("category_id")]
    public string CategoryId { get; set; } = "";

    [Column("price")]
    public decimal Price { get; set; }

    [Column("description")]
    public string? Description { get; set; }

    [Column("active")]
    public bool Active { get; set; } = true;

    [Column("has_rfid")]
    public bool HasRfid { get; set; }

    [Required]
    [Column("bay")]
    public string Bay { get; set; } = "";

    [Column("level")]
    public int Level { get; set; }

    [Column("position_index")]
    public int PositionIndex { get; set; }

    [Column("stock")]
    public int Stock { get; set; }

    [Column("created_at")]
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    [Column("updated_at")]
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;

    // Navigation properties
    public List<ProductImage> Images { get; set; } = new();
    public List<ProductRfid> Rfids { get; set; } = new();
    public List<Review> Reviews { get; set; } = new();
}

[Table("product_images")]
public class ProductImage
{
    [Key]
    [Column("product_image_id")]
    public Guid ProductImageId { get; set; }

    [Column("product_id")]
    public long ProductId { get; set; }

    [Required]
    [Column("image_url")]
    public string ImageUrl { get; set; } = "";

    [Column("image_alt_text")]
    public string? ImageAltText { get; set; }

    [Column("sort_order")]
    public int SortOrder { get; set; }

    [ForeignKey("ProductId")]
    public Product? Product { get; set; }
}

[Table("product_rfids")]
public class ProductRfid
{
    [Key]
    [Column("rfid_uid")]
    public string RfidUid { get; set; } = "";

    [Column("product_id")]
    public long ProductId { get; set; }

    [ForeignKey("ProductId")]
    public Product? Product { get; set; }
}

[Table("reviews")]
public class Review
{
    [Key]
    [Column("review_id")]
    public Guid ReviewId { get; set; }

    [Required]
    [Column("image_url")]
    public string ImageUrl { get; set; } = "";

    [Column("image_alt_text")]
    public string? ImageAltText { get; set; }

    [Column("product_id")]
    public long ProductId { get; set; }

    [Column("rating")]
    public int Rating { get; set; }

    [Column("content")]
    public string? Content { get; set; }

    [ForeignKey("ProductId")]
    public Product? Product { get; set; }
}

[Table("carts")]
public class Cart
{
    [Key]
    [Column("cart_id")]
    public int CartId { get; set; }

    [Required]
    [Column("status")]
    public string Status { get; set; } = "active";

    [Column("shopping_list")]
    public string[] ShoppingList { get; set; } = Array.Empty<string>();

    [Column("created_at")]
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    [Column("updated_at")]
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;
}
