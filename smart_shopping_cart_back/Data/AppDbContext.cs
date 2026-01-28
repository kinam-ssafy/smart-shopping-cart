using Microsoft.EntityFrameworkCore;
using smart_shopping_cart_back.Models;
using smart_shopping_cart_back.DTOs;

namespace smart_shopping_cart_back.Data;

public class AppDbContext : DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options) {}

    // Keep if your project still uses posts
    public DbSet<Post> Posts => Set<Post>();

    public DbSet<Product> Products => Set<Product>();
    public DbSet<ProductImage> ProductImages => Set<ProductImage>();
    public DbSet<Review> Reviews => Set<Review>();
    public DbSet<Cart> Carts => Set<Cart>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        modelBuilder.Entity<Product>(e =>
        {
            e.ToTable("products");
            e.HasKey(x => x.ProductId);
            e.Property(x => x.ProductId).HasColumnName("product_id");
            e.Property(x => x.CategoryId).HasColumnName("category_id");
            e.Property(x => x.PositionIndex).HasColumnName("position_index");
            e.Property(x => x.CreatedAt).HasColumnName("created_at");
            e.Property(x => x.UpdatedAt).HasColumnName("updated_at");
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
            e.Property(x => x.ShoppingList).HasColumnName("shopping_list");
            e.Property(x => x.CreatedAt).HasColumnName("created_at");
            e.Property(x => x.UpdatedAt).HasColumnName("updated_at");
        });
    }
}
