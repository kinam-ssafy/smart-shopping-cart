using Microsoft.EntityFrameworkCore;
using smart_shopping_cart_back.Data;
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
    private readonly IServiceScopeFactory _scopeFactory;

    public MapService(ILogger<MapService> logger, IServiceScopeFactory scopeFactory)
    {
        _logger = logger;
        _scopeFactory = scopeFactory;
    }

    /// <summary>
    /// 매장 지도 데이터 조회
    /// </summary>
    public async Task<MapDataDto> GetMapDataAsync(string mapId = "1")
    {
        using var scope = _scopeFactory.CreateScope();
        var context = scope.ServiceProvider.GetRequiredService<AppDbContext>();

        var result = new MapDataDto();

        // 1. 매장 경계 조회 (Raw SQL로 ST_AsText 사용)
        var storeMapQuery = await context.Database
            .SqlQueryRaw<StoreMapRaw>(@"
                SELECT 
                    store_map_id as StoreMapId,
                    version as Version,
                    ST_AsText(boundary) as BoundaryWkt,
                    units as Units
                FROM store_maps
                WHERE store_map_id = {0}
            ", mapId)
            .FirstOrDefaultAsync();

        if (storeMapQuery != null)
        {
            result.StoreMap = new StoreMapDto
            {
                Id = storeMapQuery.StoreMapId,
                Version = storeMapQuery.Version,
                Boundary = ParsePolygonWkt(storeMapQuery.BoundaryWkt),
                Units = storeMapQuery.Units
            };
        }

        // 2. 선반(fixtures) 조회 with 카테고리 정보
        var fixturesQuery = await context.Database
            .SqlQueryRaw<FixtureRaw>(@"
                SELECT 
                    f.fixture_id as FixtureId,
                    f.parent_category_id as ParentCategoryId,
                    f.label as Label,
                    ST_AsText(f.fixture_geom) as GeometryWkt,
                    pc.name as CategoryName
                FROM fixtures f
                LEFT JOIN parent_categories pc ON f.parent_category_id = pc.parent_category_id
                WHERE f.map_id = {0}
                ORDER BY f.fixture_id
            ", mapId)
            .ToListAsync();

        result.Fixtures = fixturesQuery.Select(f => new FixtureDto
        {
            Id = f.FixtureId,
            Label = f.Label ?? "",
            ParentCategoryId = f.ParentCategoryId,
            CategoryName = f.CategoryName ?? "",
            Geometry = ParsePolygonWkt(f.GeometryWkt)
        }).ToList();

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

// Raw SQL 결과 매핑용 클래스
public class StoreMapRaw
{
    public string StoreMapId { get; set; } = "";
    public string Version { get; set; } = "";
    public string? BoundaryWkt { get; set; }
    public string Units { get; set; } = "meters";
}

public class FixtureRaw
{
    public string FixtureId { get; set; } = "";
    public string ParentCategoryId { get; set; } = "";
    public string? Label { get; set; }
    public string? GeometryWkt { get; set; }
    public string? CategoryName { get; set; }
}
