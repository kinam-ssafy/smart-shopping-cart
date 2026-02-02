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

        // 2. 직선 경로가 장애물과 충돌하는지 확인 (목표 선반 제외)
        bool isBlocked = false;
        await using (var cmd = new NpgsqlCommand(@"
            SELECT EXISTS(
                SELECT 1 FROM fixtures
                WHERE fixture_id != @targetFixtureId  -- 목표 선반 제외
                AND ST_Intersects(
                    fixture_geom,
                    ST_SetSRID(ST_MakeLine(
                        ST_Point(@startX, @startY),
                        ST_Point(@endX, @endY)
                    ), 3857)
                )
            )
        ", conn))
        {
            cmd.Parameters.AddWithValue("targetFixtureId", fixtureId);
            cmd.Parameters.AddWithValue("startX", startX);
            cmd.Parameters.AddWithValue("startY", startY);
            cmd.Parameters.AddWithValue("endX", targetX);
            cmd.Parameters.AddWithValue("endY", targetY);
            
            isBlocked = (bool)(await cmd.ExecuteScalarAsync() ?? false);
            _logger.LogInformation($"[Navigation] 직선 경로 차단 여부: {isBlocked} (목표 선반 {fixtureId} 제외)");
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
            var waypoints = await GetWaypointsAroundObstacles(conn, startX, startY, targetX, targetY, fixtureId);
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
        NpgsqlConnection conn, double startX, double startY, double endX, double endY, string targetFixtureId)
    {
        var waypoints = new List<double[]>();

        // 1. 모든 후보 waypoint 수집 (모든 fixture 박스 코너들)
        var candidates = new List<(double x, double y)>();
        
        await using (var cmd = new NpgsqlCommand(@"
            SELECT 
                ST_X(ST_PointN(ST_ExteriorRing(ST_Expand(ST_Envelope(fixture_geom), 0.5)), n)) as wx,
                ST_Y(ST_PointN(ST_ExteriorRing(ST_Expand(ST_Envelope(fixture_geom), 0.5)), n)) as wy
            FROM fixtures, generate_series(1, 4) as n
        ", conn))
        {
            await using var reader = await cmd.ExecuteReaderAsync();
            while (await reader.ReadAsync())
            {
                candidates.Add((reader.GetDouble(0), reader.GetDouble(1)));
            }
        }

        if (candidates.Count == 0)
        {
            double midX = (startX + endX) / 2;
            double midY = Math.Max(startY, endY) + 1.0;
            waypoints.Add(new double[] { midX, midY });
            return waypoints;
        }

        // 2. 각 후보에 대해: 시작→후보, 후보→목표 경로가 충돌하지 않는지 검증
        var validCandidates = new List<(double x, double y, double dist)>();

        foreach (var (wx, wy) in candidates.Distinct())
        {
            bool segment1Clear = await IsPathClear(conn, startX, startY, wx, wy, targetFixtureId);
            bool segment2Clear = await IsPathClear(conn, wx, wy, endX, endY, targetFixtureId);

            if (segment1Clear && segment2Clear)
            {
                double dist = Distance(startX, startY, wx, wy) + Distance(wx, wy, endX, endY);
                validCandidates.Add((wx, wy, dist));
                _logger.LogDebug($"[Navigation] 유효한 waypoint: ({wx:F2}, {wy:F2}), 거리: {dist:F2}");
            }
        }

        // 3. 유효한 후보 중 가장 짧은 경로 선택
        if (validCandidates.Count > 0)
        {
            var best = validCandidates.OrderBy(c => c.dist).First();
            waypoints.Add(new double[] { best.x, best.y });
            _logger.LogInformation($"[Navigation] 최적 waypoint 선택: ({best.x:F2}, {best.y:F2})");
        }
        else
        {
            // 유효한 1-waypoint가 없으면, 단순 우회점 사용
            _logger.LogWarning("[Navigation] 유효한 waypoint 없음, 단순 우회점 사용");
            double midX = (startX + endX) / 2;
            double offsetY = (startY + endY) / 2 + 2.0; // 중간점에서 약간 오프셋
            waypoints.Add(new double[] { midX, offsetY });
        }

        return waypoints;
    }

    /// <summary>
    /// 두 점 사이의 경로가 장애물과 충돌하지 않는지 확인 (목표 선반 제외)
    /// </summary>
    private async Task<bool> IsPathClear(NpgsqlConnection conn, double x1, double y1, double x2, double y2, string targetFixtureId)
    {
        await using var cmd = new NpgsqlCommand(@"
            SELECT NOT EXISTS(
                SELECT 1 FROM fixtures
                WHERE fixture_id != @targetFixtureId
                AND ST_Intersects(
                    fixture_geom,
                    ST_SetSRID(ST_MakeLine(
                        ST_Point(@x1, @y1),
                        ST_Point(@x2, @y2)
                    ), 3857)
                )
            )
        ", conn);

        cmd.Parameters.AddWithValue("targetFixtureId", targetFixtureId);
        cmd.Parameters.AddWithValue("x1", x1);
        cmd.Parameters.AddWithValue("y1", y1);
        cmd.Parameters.AddWithValue("x2", x2);
        cmd.Parameters.AddWithValue("y2", y2);

        return (bool)(await cmd.ExecuteScalarAsync() ?? false);
    }

    /// <summary>
    /// 두 점 사이의 유클리드 거리
    /// </summary>
    private static double Distance(double x1, double y1, double x2, double y2)
    {
        return Math.Sqrt(Math.Pow(x2 - x1, 2) + Math.Pow(y2 - y1, 2));
    }
}
