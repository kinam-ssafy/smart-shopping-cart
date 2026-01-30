using Microsoft.EntityFrameworkCore;
using smart_shopping_cart_back.Models;

namespace smart_shopping_cart_back.Data;

public class AppDbContext : DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options) { }

    // Core entities
    public DbSet<Product> Products { get; set; }
    public DbSet<ProductImage> ProductImages { get; set; }
    public DbSet<ProductRfid> ProductRfids { get; set; }
    public DbSet<Review> Reviews { get; set; }
    public DbSet<Cart> Carts { get; set; }
    public DbSet<RagChunk> RagChunks { get; set; }

    // Map entities
    public DbSet<StoreMap> StoreMaps { get; set; }
    public DbSet<Fixture> Fixtures { get; set; }
    public DbSet<ParentCategory> ParentCategories { get; set; }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        // Require Pgvector extension
        modelBuilder.HasPostgresExtension("vector");

        base.OnModelCreating(modelBuilder);

        // Product entity configuration
        modelBuilder.Entity<Product>(e =>
        {
            e.ToTable("products");
            e.HasKey(x => x.ProductId);
            e.Property(x => x.ProductId).HasColumnName("product_id");
            e.Property(x => x.CategoryId).HasColumnName("category_id");
            e.Property(x => x.PositionIndex).HasColumnName("position_index");
            e.Property(x => x.CreatedAt).HasColumnName("created_at");
            e.Property(x => x.UpdatedAt).HasColumnName("updated_at");

            // Relationships
            e.HasMany(p => p.Images)
                .WithOne(i => i.Product)
                .HasForeignKey(i => i.ProductId);

            e.HasMany(p => p.Rfids)
                .WithOne(r => r.Product)
                .HasForeignKey(r => r.ProductId);

            e.HasMany(p => p.Reviews)
                .WithOne(r => r.Product)
                .HasForeignKey(r => r.ProductId);
        });

        modelBuilder.Entity<ProductImage>(e =>
        {
            e.ToTable("product_images");
            e.HasKey(x => x.ProductImageId);
            e.Property(x => x.ProductImageId).HasColumnName("product_image_id");
            e.Property(x => x.ProductId).HasColumnName("product_id");
            e.Property(x => x.ImageUrl).HasColumnName("image_url");
            e.Property(x => x.ImageAltText).HasColumnName("image_alt_text");
            e.Property(x => x.SortOrder).HasColumnName("sort_order");
            e.Property(x => x.CreatedAt).HasColumnName("created_at");
        });

        modelBuilder.Entity<Review>(e =>
        {
            e.ToTable("reviews");
            e.HasKey(x => x.ReviewId);
            e.Property(x => x.ReviewId).HasColumnName("review_id");
            e.Property(x => x.ProductId).HasColumnName("product_id");
            e.Property(x => x.ImageUrl).HasColumnName("image_url");
            e.Property(x => x.ImageAltText).HasColumnName("image_alt_text");
            e.Property(x => x.Rating).HasColumnName("rating");
            e.Property(x => x.Content).HasColumnName("content");
            e.Property(x => x.CreatedAt).HasColumnName("created_at");
        });

        modelBuilder.Entity<Cart>(e =>
        {
            e.ToTable("carts");
            e.HasKey(x => x.CartId);
            e.Property(x => x.CartId).HasColumnName("cart_id");
            e.Property(x => x.Status).HasColumnName("status");
            e.Property(x => x.ShoppingList).HasColumnName("shopping_list").HasColumnType("text[]");
            e.Property(x => x.CreatedAt).HasColumnName("created_at");
            e.Property(x => x.UpdatedAt).HasColumnName("updated_at");
        });
    }
}
