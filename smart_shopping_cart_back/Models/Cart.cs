using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace smart_shopping_cart_back.Models;

[Table("carts")]
public class Cart
{
    [Key]
    [Column("cart_id")]
    public int CartId { get; set; }

    [Column("status")]
    public string Status { get; set; } = "active";

    [Column("shopping_list")]
    public string[]? ShoppingList { get; set; }

    [Column("created_at")]
    public DateTimeOffset CreatedAt { get; set; }

    [Column("updated_at")]
    public DateTimeOffset UpdatedAt { get; set; }
}
