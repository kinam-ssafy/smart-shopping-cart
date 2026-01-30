using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace smart_shopping_cart_back.Models;

// ============================================================
// Product, ProductImage, ProductRfid, Review, Cart 클래스는
// 개별 파일로 분리됨 (Product.cs, ProductImage.cs 등)
// ============================================================

// ============================================================
// ProductRfid (개별 파일 없음 - 여기에 유지)
// ============================================================
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

// ============================================================
// Map & Fixture Entities
// ============================================================

[Table("store_maps")]
public class StoreMap
{
    [Key]
    [Column("store_map_id")]
    public string StoreMapId { get; set; } = "1";

    [Column("version")]
    public string Version { get; set; } = "1";

    [Column("boundary")]
    public byte[] Boundary { get; set; } = Array.Empty<byte>(); // PostGIS geometry stored as WKB

    [Column("units")]
    public string Units { get; set; } = "meters";

    [Column("created_at")]
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
}

[Table("parent_categories")]
public class ParentCategory
{
    [Key]
    [Column("parent_category_id")]
    public string ParentCategoryId { get; set; } = "";

    [Required]
    [Column("name")]
    public string Name { get; set; } = "";

    [Column("created_at")]
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    // Navigation
    public Fixture? Fixture { get; set; }
}

[Table("fixtures")]
public class Fixture
{
    [Column("fixture_id")]
    public string FixtureId { get; set; } = "";

    [Key]
    [Column("parent_category_id")]
    public string ParentCategoryId { get; set; } = "";

    [Column("map_id")]
    public string MapId { get; set; } = "1";

    [Column("fixture_geom")]
    public byte[] FixtureGeom { get; set; } = Array.Empty<byte>(); // PostGIS geometry stored as WKB

    [Column("label")]
    public string? Label { get; set; }

    // Navigation
    [ForeignKey("ParentCategoryId")]
    public ParentCategory? ParentCategory { get; set; }

    [ForeignKey("MapId")]
    public StoreMap? StoreMap { get; set; }
}
