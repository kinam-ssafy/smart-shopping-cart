using Microsoft.EntityFrameworkCore;
using smart_shopping_cart_back.Models;

namespace smart_shopping_cart_back.Data;

public class AppDbContext : DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options)
    {
    }

    public DbSet<Product> Products { get; set; }
    public DbSet<ProductImage> ProductImages { get; set; }
    public DbSet<ProductRfid> ProductRfids { get; set; }
    public DbSet<Review> Reviews { get; set; }
    public DbSet<Cart> Carts { get; set; }
    public DbSet<RagChunk> RagChunks { get; set; }

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        // Require Pgvector extension
        modelBuilder.HasPostgresExtension("vector");

        base.OnModelCreating(modelBuilder);

        // Configure One-to-Many relationships
        modelBuilder.Entity<Product>()
            .HasMany(p => p.Images)
            .WithOne(i => i.Product)
            .HasForeignKey(i => i.ProductId);

        modelBuilder.Entity<Product>()
            .HasMany(p => p.Rfids)
            .WithOne(r => r.Product)
            .HasForeignKey(r => r.ProductId);

        modelBuilder.Entity<Product>()
            .HasMany(p => p.Reviews)
            .WithOne(r => r.Product)
            .HasForeignKey(r => r.ProductId);

        // Configure Postgres Array for ShoppingList
        modelBuilder.Entity<Cart>()
            .Property(c => c.ShoppingList)
            .HasColumnType("text[]");
    }
}
