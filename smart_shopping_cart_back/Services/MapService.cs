using Npgsql;
using smart_shopping_cart_back.Models;

namespace smart_shopping_cart_back.Services;

/// <summary>
/// 매장 지도 서비스
/// - store_maps, fixtures 조회
/// - PostGIS geometry → 좌표 배열 변환
/// </summary>
public class MapService
{
    private readonly ILogger<MapService> _logger;
    private readonly IConfiguration _configuration;

    public MapService(ILogger<MapService> logger, IConfiguration configuration)
    {
        _logger = logger;
        _configuration = configuration;
    }

    /// <summary>
    /// 매장 지도 데이터 조회
    /// </summary>
    public async Task<MapDataDto> GetMapDataAsync(string mapId = "1")
    {
        var result = new MapDataDto();
        var connectionString = _configuration.GetConnectionString("DefaultConnection");

        await using var conn = new NpgsqlConnection(connectionString);
        await conn.OpenAsync();

        // 1. 매장 경계 조회
        await using (var cmd = new NpgsqlCommand(@"
            SELECT 
                store_map_id,
                version,
                ST_AsText(boundary) as boundary_wkt,
                units
            FROM store_maps
            WHERE store_map_id = @mapId
        ", conn))
        {
            cmd.Parameters.AddWithValue("mapId", mapId);

            await using var reader = await cmd.ExecuteReaderAsync();
            if (await reader.ReadAsync())
            {
                result.StoreMap = new StoreMapDto
                {
                    Id = reader.GetString(0),
                    Version = reader.GetString(1),
                    Boundary = ParsePolygonWkt(reader.IsDBNull(2) ? null : reader.GetString(2)),
                    Units = reader.GetString(3)
                };
            }
        }

        // 2. 선반(fixtures) 조회 with 카테고리 정보
        await using (var cmd = new NpgsqlCommand(@"
            SELECT 
                f.fixture_id,
                f.parent_category_id,
                f.label,
                ST_AsText(f.fixture_geom) as geometry_wkt,
                pc.name as category_name
            FROM fixtures f
            LEFT JOIN parent_categories pc ON f.parent_category_id = pc.parent_category_id
            WHERE f.map_id = @mapId
            ORDER BY f.fixture_id
        ", conn))
        {
            cmd.Parameters.AddWithValue("mapId", mapId);

            await using var reader = await cmd.ExecuteReaderAsync();
            while (await reader.ReadAsync())
            {
                result.Fixtures.Add(new FixtureDto
                {
                    Id = reader.GetString(0),
                    ParentCategoryId = reader.GetString(1),
                    Label = reader.IsDBNull(2) ? "" : reader.GetString(2),
                    Geometry = ParsePolygonWkt(reader.IsDBNull(3) ? null : reader.GetString(3)),
                    CategoryName = reader.IsDBNull(4) ? "" : reader.GetString(4)
                });
            }
        }

        _logger.LogInformation($"[MapService] 지도 조회 완료: {result.Fixtures.Count}개 선반");

        return result;
    }

    /// <summary>
    /// WKT (Well-Known Text) 형식의 Polygon을 좌표 배열로 변환
    /// 예: "POLYGON((x1 y1, x2 y2, ...))" → [[x1, y1], [x2, y2], ...]
    /// </summary>
    private List<double[]> ParsePolygonWkt(string? wkt)
    {
        var coords = new List<double[]>();
        if (string.IsNullOrEmpty(wkt)) return coords;

        try
        {
            // MULTIPOLYGON(((x y, ...))) 또는 POLYGON((x y, ...)) 파싱
            var content = wkt;
            
            // MULTIPOLYGON 처리
            if (content.StartsWith("MULTIPOLYGON"))
            {
                content = content.Replace("MULTIPOLYGON(((", "").Replace(")))", "");
            }
            // POLYGON 처리
            else if (content.StartsWith("POLYGON"))
            {
                content = content.Replace("POLYGON((", "").Replace("))", "");
            }

            // 좌표 파싱
            var pairs = content.Split(',');
            foreach (var pair in pairs)
            {
                var trimmed = pair.Trim();
                var parts = trimmed.Split(' ');
                if (parts.Length >= 2 &&
                    double.TryParse(parts[0], out var x) &&
                    double.TryParse(parts[1], out var y))
                {
                    coords.Add(new[] { x, y });
                }
            }
        }
        catch (Exception ex)
        {
            _logger.LogWarning($"[MapService] WKT 파싱 실패: {ex.Message}");
        }

        return coords;
    }
}

