using Npgsql;
using System.Text.Json;

namespace smart_shopping_cart_back.Services;

/// <summary>
/// 카트 상품 DTO (프론트엔드 전송용)
/// </summary>
public class CartProductDto
{
    public long Id { get; set; }
    public string Name { get; set; } = "";
    public decimal Price { get; set; }
    public string? Image { get; set; }
    public int Quantity { get; set; } = 1;
    public decimal Rating { get; set; }
    public string? Location { get; set; }
    public bool HasRfid { get; set; }
    public string? RfidUid { get; set; }
    public CartProductDetailDto? Detail { get; set; }
}

public class CartProductDetailDto
{
    public List<string> Images { get; set; } = new();
    public string Description { get; set; } = "";
    public decimal AverageRating { get; set; }
    public List<ReviewDto> Reviews { get; set; } = new();
}

public class ReviewDto
{
    public decimal Rating { get; set; }
    public string Content { get; set; } = "";
    public List<string>? Images { get; set; }
}

/// <summary>
/// 카트 DB 서비스
/// - RFID UID로 상품 조회
/// - 카트에 상품 목록 저장
/// </summary>
public class CartDbService
{
    private readonly ILogger<CartDbService> _logger;
    private readonly string _connectionString;

    public CartDbService(ILogger<CartDbService> logger, IConfiguration configuration)
    {
        _logger = logger;
        _connectionString = configuration.GetConnectionString("DefaultConnection") 
            ?? "Host=localhost;Port=5432;Database=smart_cart;Username=postgres;Password=password";
    }

    /// <summary>
    /// RFID UID 배열로 상품 상세 정보 조회 (프론트엔드 DTO 형식)
    /// </summary>
    public async Task<List<CartProductDto>> GetProductsByRfidUidsAsync(string[] rfidUids)
    {
        var products = new List<CartProductDto>();

        if (rfidUids.Length == 0)
            return products;

        await using var conn = new NpgsqlConnection(_connectionString);
        await conn.OpenAsync();

        // RFID UID로 상품 정보 조회
        var sql = @"
            SELECT 
                p.product_id, p.name, p.price, p.description, p.has_rfid,
                p.bay, p.level, p.position_index,
                r.rfid_uid,
                (SELECT AVG(rating) FROM reviews WHERE product_id = p.product_id) as avg_rating
            FROM products p
            INNER JOIN product_rfids r ON p.product_id = r.product_id
            WHERE r.rfid_uid = ANY(@uids)";

        await using var cmd = new NpgsqlCommand(sql, conn);
        cmd.Parameters.AddWithValue("uids", rfidUids);

        await using var reader = await cmd.ExecuteReaderAsync();
        while (await reader.ReadAsync())
        {
            var productId = reader.GetInt64(0);
            var bay = reader.IsDBNull(5) ? "" : reader.GetString(5);
            var level = reader.IsDBNull(6) ? 0 : reader.GetInt32(6);
            var positionIndex = reader.IsDBNull(7) ? 0 : reader.GetInt32(7);

            products.Add(new CartProductDto
            {
                Id = productId,
                Name = reader.GetString(1),
                Price = reader.GetDecimal(2),
                Rating = reader.IsDBNull(9) ? 0 : reader.GetDecimal(9),
                HasRfid = reader.GetBoolean(4),
                RfidUid = reader.IsDBNull(8) ? null : reader.GetString(8),
                Location = string.IsNullOrEmpty(bay) ? null : $"{bay}-{level}",
                Detail = new CartProductDetailDto
                {
                    Description = reader.IsDBNull(3) ? "" : reader.GetString(3),
                    AverageRating = reader.IsDBNull(9) ? 0 : reader.GetDecimal(9),
                    Images = new List<string>(),
                    Reviews = new List<ReviewDto>()
                }
            });
        }

        // 상품 이미지 조회
        await reader.CloseAsync();
        foreach (var product in products)
        {
            product.Image = await GetFirstProductImageAsync(conn, product.Id);
            if (product.Detail != null)
            {
                product.Detail.Images = await GetProductImagesAsync(conn, product.Id);
                product.Detail.Reviews = await GetProductReviewsAsync(conn, product.Id);
            }
        }

        return products;
    }

    private async Task<string?> GetFirstProductImageAsync(NpgsqlConnection conn, long productId)
    {
        var sql = "SELECT image_url FROM product_images WHERE product_id = @id ORDER BY sort_order LIMIT 1";
        await using var cmd = new NpgsqlCommand(sql, conn);
        cmd.Parameters.AddWithValue("id", productId);
        var result = await cmd.ExecuteScalarAsync();
        return result as string;
    }

    private async Task<List<string>> GetProductImagesAsync(NpgsqlConnection conn, long productId)
    {
        var images = new List<string>();
        var sql = "SELECT image_url FROM product_images WHERE product_id = @id ORDER BY sort_order";
        await using var cmd = new NpgsqlCommand(sql, conn);
        cmd.Parameters.AddWithValue("id", productId);
        await using var reader = await cmd.ExecuteReaderAsync();
        while (await reader.ReadAsync())
        {
            images.Add(reader.GetString(0));
        }
        return images;
    }

    private async Task<List<ReviewDto>> GetProductReviewsAsync(NpgsqlConnection conn, long productId)
    {
        var reviews = new List<ReviewDto>();
        var sql = "SELECT rating, content, image_url FROM reviews WHERE product_id = @id LIMIT 5";
        await using var cmd = new NpgsqlCommand(sql, conn);
        cmd.Parameters.AddWithValue("id", productId);
        await using var reader = await cmd.ExecuteReaderAsync();
        while (await reader.ReadAsync())
        {
            reviews.Add(new ReviewDto
            {
                Rating = reader.GetDecimal(0),
                Content = reader.GetString(1),
                Images = reader.IsDBNull(2) ? null : new List<string> { reader.GetString(2) }
            });
        }
        return reviews;
    }

    /// <summary>
    /// RFID UID 배열을 받아 해당 상품 ID 목록을 반환
    /// </summary>
    public async Task<List<long>> GetProductIdsByRfidUidsAsync(string[] rfidUids)
    {
        var productIds = new List<long>();

        if (rfidUids.Length == 0)
            return productIds;

        await using var conn = new NpgsqlConnection(_connectionString);
        await conn.OpenAsync();

        var sql = "SELECT product_id FROM product_rfids WHERE rfid_uid = ANY(@uids)";
        await using var cmd = new NpgsqlCommand(sql, conn);
        cmd.Parameters.AddWithValue("uids", rfidUids);

        await using var reader = await cmd.ExecuteReaderAsync();
        while (await reader.ReadAsync())
        {
            productIds.Add(reader.GetInt64(0));
        }

        return productIds;
    }

    /// <summary>
    /// 카트에 상품 목록 업데이트
    /// </summary>
    public async Task UpdateCartItemsAsync(int cartId, string[] rfidUids)
    {
        await using var conn = new NpgsqlConnection(_connectionString);
        await conn.OpenAsync();

        var sql = @"
            UPDATE carts 
            SET shopping_list = @items, updated_at = NOW() 
            WHERE cart_id = @cartId";

        await using var cmd = new NpgsqlCommand(sql, conn);
        cmd.Parameters.AddWithValue("items", rfidUids);
        cmd.Parameters.AddWithValue("cartId", cartId);

        var affected = await cmd.ExecuteNonQueryAsync();
        
        if (affected == 0)
        {
            var insertSql = @"
                INSERT INTO carts (cart_id, status, shopping_list) 
                VALUES (@cartId, 'active', @items)
                ON CONFLICT (cart_id) DO UPDATE SET shopping_list = @items, updated_at = NOW()";

            await using var insertCmd = new NpgsqlCommand(insertSql, conn);
            insertCmd.Parameters.AddWithValue("items", rfidUids);
            insertCmd.Parameters.AddWithValue("cartId", cartId);
            await insertCmd.ExecuteNonQueryAsync();
        }

        _logger.LogInformation($"[CartDB] 카트 {cartId} 업데이트: {rfidUids.Length}개 아이템");
    }

    /// <summary>
    /// 카트 상품 목록 조회 (RFID UID 배열)
    /// </summary>
    public async Task<string[]> GetCartItemsAsync(int cartId)
    {
        await using var conn = new NpgsqlConnection(_connectionString);
        await conn.OpenAsync();

        var sql = "SELECT shopping_list FROM carts WHERE cart_id = @cartId";
        await using var cmd = new NpgsqlCommand(sql, conn);
        cmd.Parameters.AddWithValue("cartId", cartId);

        var result = await cmd.ExecuteScalarAsync();
        
        if (result is string[] items)
            return items;
        
        return Array.Empty<string>();
    }

    /// <summary>
    /// 카트 상품 상세 정보 조회 (프론트엔드용)
    /// </summary>
    public async Task<List<CartProductDto>> GetCartProductsAsync(int cartId)
    {
        var rfidUids = await GetCartItemsAsync(cartId);
        return await GetProductsByRfidUidsAsync(rfidUids);
    }
}
