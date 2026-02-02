using Npgsql;
using smart_shopping_cart_back.Models;

namespace smart_shopping_cart_back.Services;

/// <summary>
/// 네비게이션 서비스 (PostGIS 기반)
/// - PostGIS geometry 함수를 사용한 경로 계산
/// - 장애물(선반) 회피 경로 생성
/// </summary>
public class NavigationService
{
    private readonly IConfiguration _configuration;
    private readonly PositionService _positionService;
    private readonly CartDbService _cartDbService;
    private readonly ILogger<NavigationService> _logger;

    public NavigationService(
        IConfiguration configuration,
        PositionService positionService,
        CartDbService cartDbService,
        ILogger<NavigationService> logger)
    {
        _configuration = configuration;
        _positionService = positionService;
        _cartDbService = cartDbService;
        _logger = logger;
    }

    /// <summary>
    /// 현재 위치에서 특정 상품(선반)까지의 경로 계산
    /// </summary>
    public async Task<List<double[]>> GetPathToProductAsync(long productId)
    {
        // 1. 현재 위치 가져오기 (stale 체크 포함)
        var currentPos = _positionService.CurrentPosition;
        if (currentPos == null || _positionService.IsPositionStale)
        {
            _logger.LogWarning("[Navigation] 위치 없음 or 오래됨. 기본 위치(1, 1) 사용");
            currentPos = new CartPositionDto { X = 1.0, Y = 1.0, Theta = 0 };
        }

        // 2. 상품 정보 조회 → 목표 선반(Bay) 확인
        var product = await _cartDbService.GetProductByIdAsync(productId);
        if (product == null || string.IsNullOrEmpty(product.Location))
        {
            _logger.LogWarning($"[Navigation] 상품 {productId} 위치 정보 없음");
            return new List<double[]>();
        }

        var targetBay = product.Location.Split('-')[0]; // "D-2-0" → "D"
        _logger.LogInformation($"[Navigation] 시작: ({currentPos.X:F2}, {currentPos.Y:F2}) → Bay {targetBay}");

        // 3. PostGIS로 경로 계산
        var path = await CalculatePathWithPostGIS(currentPos.X, currentPos.Y, targetBay);
        
        _logger.LogInformation($"[Navigation] 경로 계산 완료: {path.Count}개 waypoint");
        return path;
    }

    /// <summary>
    /// PostGIS를 사용하여 경로 계산
    /// - 직선 경로가 장애물과 충돌하면 waypoint 추가
    /// </summary>
    private async Task<List<double[]>> CalculatePathWithPostGIS(double startX, double startY, string targetBay)
    {
        var path = new List<double[]>();
        var connectionString = _configuration.GetConnectionString("DefaultConnection");

        await using var conn = new NpgsqlConnection(connectionString);
        await conn.OpenAsync();

        // 1. 목표 선반 중심점 조회
        // fixture_id는 'shelf-a', 'shelf-b' ... 형태
        double targetX = 0, targetY = 0;
        string fixtureId = $"shelf-{targetBay.ToLower()}";
        _logger.LogInformation($"[Navigation] 상품 위치에서 추출한 Bay: '{targetBay}' → fixture_id: '{fixtureId}'");
        
        await using (var cmd = new NpgsqlCommand(@"
            SELECT 
                fixture_id,
                label,
                ST_X(ST_Centroid(fixture_geom)) as center_x,
                ST_Y(ST_Centroid(fixture_geom)) as center_y
            FROM fixtures
            WHERE fixture_id = @fixtureId
            LIMIT 1
        ", conn))
        {
            cmd.Parameters.AddWithValue("fixtureId", fixtureId);
            await using var reader = await cmd.ExecuteReaderAsync();
            if (await reader.ReadAsync())
            {
                var foundId = reader.GetString(0);
                var foundLabel = reader.GetString(1);
                targetX = reader.GetDouble(2);
                targetY = reader.GetDouble(3);
                _logger.LogInformation($"[Navigation] 찾은 선반: id='{foundId}', label='{foundLabel}', 중심=({targetX:F3}, {targetY:F3})");
            }
            else
            {
                _logger.LogWarning($"[Navigation] fixture_id '{fixtureId}' 없음. DB fixtures 확인 필요!");
                return path;
            }
        }

        // 2. 직선 경로가 장애물과 충돌하는지 확인
        bool isBlocked = false;
        await using (var cmd = new NpgsqlCommand(@"
            SELECT EXISTS(
                SELECT 1 FROM fixtures
                WHERE ST_Intersects(
                    fixture_geom,
                    ST_SetSRID(ST_MakeLine(
                        ST_Point(@startX, @startY),
                        ST_Point(@endX, @endY)
                    ), 3857)
                )
            )
        ", conn))
        {
            cmd.Parameters.AddWithValue("startX", startX);
            cmd.Parameters.AddWithValue("startY", startY);
            cmd.Parameters.AddWithValue("endX", targetX);
            cmd.Parameters.AddWithValue("endY", targetY);
            
            isBlocked = (bool)(await cmd.ExecuteScalarAsync() ?? false);
            _logger.LogInformation($"[Navigation] 직선 경로 차단 여부: {isBlocked}");
        }

        // 시작점 추가
        path.Add(new double[] { startX, startY });

        if (!isBlocked)
        {
            // 3a. 직선 경로 사용 (장애물 없음)
            path.Add(new double[] { targetX, targetY });
        }
        else
        {
            // 3b. 장애물 회피 경로 계산
            // 간단한 방식: 선반 외곽의 가장 가까운 점을 waypoint로 사용
            var waypoints = await GetWaypointsAroundObstacles(conn, startX, startY, targetX, targetY);
            path.AddRange(waypoints);
            path.Add(new double[] { targetX, targetY });
        }

        return path;
    }

    /// <summary>
    /// 장애물 주변의 waypoint 계산
    /// - 충돌하는 선반의 외곽을 우회하는 점 생성
    /// </summary>
    private async Task<List<double[]>> GetWaypointsAroundObstacles(
        NpgsqlConnection conn, double startX, double startY, double endX, double endY)
    {
        var waypoints = new List<double[]>();

        // 1. 모든 후보 waypoint 수집 (blocking fixture 박스 코너들)
        var candidates = new List<(double x, double y)>();
        
        await using (var cmd = new NpgsqlCommand(@"
            WITH blocking_fixtures AS (
                SELECT fixture_geom, 
                       ST_Expand(ST_Envelope(fixture_geom), 0.5) as expanded_box
                FROM fixtures
                WHERE ST_Intersects(
                    fixture_geom,
                    ST_SetSRID(ST_MakeLine(
                        ST_Point(@startX, @startY),
                        ST_Point(@endX, @endY)
                    ), 3857)
                )
            )
            SELECT 
                ST_X(ST_PointN(ST_ExteriorRing(expanded_box), n)) as wx,
                ST_Y(ST_PointN(ST_ExteriorRing(expanded_box), n)) as wy
            FROM blocking_fixtures, generate_series(1, 4) as n
        ", conn))
        {
            cmd.Parameters.AddWithValue("startX", startX);
            cmd.Parameters.AddWithValue("startY", startY);
            cmd.Parameters.AddWithValue("endX", endX);
            cmd.Parameters.AddWithValue("endY", endY);

            await using var reader = await cmd.ExecuteReaderAsync();
            while (await reader.ReadAsync())
            {
                candidates.Add((reader.GetDouble(0), reader.GetDouble(1)));
            }
        }

        if (candidates.Count == 0)
        {
            // 후보가 없으면 우회점 하나 추가
            double midX = (startX + endX) / 2;
            double midY = Math.Max(startY, endY) + 1.0;
            waypoints.Add(new double[] { midX, midY });
            return waypoints;
        }

        // 2. 각 후보로 1-waypoint 경로 시도, 가장 짧은 것 선택
        double bestSingleDist = double.MaxValue;
        (double x, double y)? bestSingle = null;

        foreach (var (wx, wy) in candidates)
        {
            double dist = Distance(startX, startY, wx, wy) + Distance(wx, wy, endX, endY);
            if (dist < bestSingleDist)
            {
                bestSingleDist = dist;
                bestSingle = (wx, wy);
            }
        }

        // 3. 직선 거리와 비교 - 1-waypoint가 직선보다 1.5배 이상 길면 더 스마트하게
        double directDist = Distance(startX, startY, endX, endY);
        
        if (bestSingle.HasValue && bestSingleDist < directDist * 2.0)
        {
            // 1-waypoint 경로가 합리적이면 사용
            waypoints.Add(new double[] { bestSingle.Value.x, bestSingle.Value.y });
            _logger.LogDebug($"[Navigation] 1-waypoint 선택: ({bestSingle.Value.x:F2}, {bestSingle.Value.y:F2}), 거리: {bestSingleDist:F2}");
        }
        else
        {
            // 2-waypoint 필요 - 가장 가까운 2개 선택
            var sorted = candidates
                .OrderBy(c => Distance(startX, startY, c.x, c.y) + Distance(c.x, c.y, endX, endY))
                .Take(2)
                .ToList();

            foreach (var (wx, wy) in sorted)
            {
                waypoints.Add(new double[] { wx, wy });
                _logger.LogDebug($"[Navigation] 2-waypoint 추가: ({wx:F2}, {wy:F2})");
            }
        }

        return waypoints;
    }

    /// <summary>
    /// 두 점 사이의 유클리드 거리
    /// </summary>
    private static double Distance(double x1, double y1, double x2, double y2)
    {
        return Math.Sqrt(Math.Pow(x2 - x1, 2) + Math.Pow(y2 - y1, 2));
    }
}
