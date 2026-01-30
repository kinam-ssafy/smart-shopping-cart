using System.Drawing;
using smart_shopping_cart_back.Models;

namespace smart_shopping_cart_back.Services;

/// <summary>
/// 네비게이션 서비스
/// - A* 알고리즘을 사용한 경로 탐색
/// - 매장 지도를 그리드로 변환하여 장애물(선반) 회피
/// </summary>
public class NavigationService
{
    private readonly MapService _mapService;
    private readonly PositionService _positionService;
    private readonly ILogger<NavigationService> _logger;
    private readonly IConfiguration _configuration;

    private readonly CartDbService _cartDbService;

    // 그리드 설정 (0.25m 단위)
    private const double GridSize = 0.25; 
    private const int MapWidthCells = 60;  // 15m
    private const int MapHeightCells = 60; // 15m

    public NavigationService(
        MapService mapService, 
        PositionService positionService, 
        CartDbService cartDbService,
        ILogger<NavigationService> logger,
        IConfiguration configuration)
    {
        _mapService = mapService;
        _positionService = positionService;
        _cartDbService = cartDbService;
        _logger = logger;
        _configuration = configuration;
    }

    /// <summary>
    /// 현재 위치에서 특정 상품(상품이 있는 선반)까지의 경로 계산
    /// </summary>
    public async Task<List<double[]>> GetPathToProductAsync(long productId)
    {
        // 1. 현재 위치
        var currentPos = _positionService.CurrentPosition;
        if (currentPos == null)
        {
            _logger.LogWarning("[Navigation] 현재 위치 불명");
            return new List<double[]>();
        }

        // 2. 상품 정보 조회
        var product = await _cartDbService.GetProductByIdAsync(productId);
        if (product == null || string.IsNullOrEmpty(product.Location))
        {
             _logger.LogWarning($"[Navigation] 상품 정보를 찾을 수 없음: {productId}");
             return new List<double[]>();
        }

        // Location 포맷: "A-1-2" (Bay-Level-Index)
        var parts = product.Location.Split('-');
        var targetBay = parts.Length > 0 ? parts[0] : ""; // 예: "A"

        // 3. 지도 및 장애물 가져오기
        var mapData = await _mapService.GetMapDataAsync();
        var obstacles = mapData.Fixtures;

        // 4. 목표 선반(Fixture) 찾기
        FixtureDto? targetFixture = null;
        
        // Bay A -> "Bay A" 포함하는 라벨 찾기 (단순화)
        targetFixture = obstacles.FirstOrDefault(f => f.Label.Contains($"Bay {targetBay}", StringComparison.OrdinalIgnoreCase)) 
                        ?? obstacles.FirstOrDefault(f => f.Label.Contains(targetBay, StringComparison.OrdinalIgnoreCase));

        if (targetFixture == null)
        {
            _logger.LogWarning($"[Navigation] 목표 선반을 찾을 수 없음: Bay {targetBay}");
            // 실패 시 그냥 빈 경로 (또는 임시 위치)
            return new List<double[]>();
        }

        // 목표 지점: 선반의 중심점
        // 하지만 선반 내부로 들어가면 안 되므로, 선반 주변 접근점(Access Point)을 찾아야 함.
        // 여기서는 간단히 중심점에서 가장 가까운 "이동 가능" 그리드 셀을 찾도록 A* 내부에서 처리 가능.
        // 우선 중심점 계산
        var center = GetPolygonCenter(targetFixture.Geometry);
        var targetPoint = new PointF((float)center[0], (float)center[1]);

        // 5. A* 알고리즘 실행
        var startPoint = new PointF((float)currentPos.X, (float)currentPos.Y);
        
        // 그리드 생성 및 장애물 마킹
        var grid = CreateGrid(obstacles);
        
        // 경로 탐색
        var path = FindPathAStar(grid, startPoint, targetPoint);

        return path;
    }

    // --- Helper Methods ---

    private double[] GetPolygonCenter(List<double[]> polygon)
    {
        if (polygon.Count == 0) return new double[] { 0, 0 };
        double sumX = 0, sumY = 0;
        foreach (var p in polygon)
        {
            sumX += p[0];
            sumY += p[1];
        }
        return new double[] { sumX / polygon.Count, sumY / polygon.Count };
    }

    private bool[,] CreateGrid(List<FixtureDto> obstacles)
    {
        var grid = new bool[MapWidthCells, MapHeightCells]; // false: 이동 가능, true: 장애물

        foreach (var obstacle in obstacles)
        {
            // 폴리곤 내부 그리드 셀 마킹 (간단한 Bounding Box + Point In Polygon)
            MarkPolygonOnGrid(grid, obstacle.Geometry);
        }

        return grid;
    }

    private void MarkPolygonOnGrid(bool[,] grid, List<double[]> polygon)
    {
        if (polygon.Count < 3) return;

        // Bounding Box
        double minX = polygon.Min(p => p[0]);
        double maxX = polygon.Max(p => p[0]);
        double minY = polygon.Min(p => p[1]);
        double maxY = polygon.Max(p => p[1]);

        int startX = Math.Max(0, (int)(minX / GridSize));
        int endX = Math.Min(MapWidthCells - 1, (int)(maxX / GridSize));
        int startY = Math.Max(0, (int)(minY / GridSize));
        int endY = Math.Min(MapHeightCells - 1, (int)(maxY / GridSize));

        for (int x = startX; x <= endX; x++)
        {
            for (int y = startY; y <= endY; y++)
            {
                double worldX = x * GridSize + GridSize / 2;
                double worldY = y * GridSize + GridSize / 2;

                if (IsPointInPolygon(worldX, worldY, polygon))
                {
                    grid[x, y] = true; // 장애물
                }
            }
        }
    }

    // Ray casting algorithm
    private bool IsPointInPolygon(double x, double y, List<double[]> polygon)
    {
        bool inside = false;
        for (int i = 0, j = polygon.Count - 1; i < polygon.Count; j = i++)
        {
            if (((polygon[i][1] > y) != (polygon[j][1] > y)) &&
                (x < (polygon[j][0] - polygon[i][0]) * (y - polygon[i][1]) / (polygon[j][1] - polygon[i][1]) + polygon[i][0]))
            {
                inside = !inside;
            }
        }
        return inside;
    }

    private List<double[]> FindPathAStar(bool[,] grid, PointF start, PointF end)
    {
        // 1. 그리드 좌표 변환
        var startNode = new Point((int)(start.X / GridSize), (int)(start.Y / GridSize));
        var endNode = new Point((int)(end.X / GridSize), (int)(end.Y / GridSize));

        // 범위 체크
        if (!IsValid(startNode)) return new List<double[]>();
        
        // 목표 지점이 장애물 내부라면, 가장 가까운 이동 가능 지점으로 변경
        if (!IsValid(endNode) || grid[endNode.X, endNode.Y])
        {
            endNode = FindNearestWalkableNode(grid, endNode);
            if (!IsValid(endNode)) return new List<double[]>();
        }

        // A* 초기화
        var openSet = new PriorityQueue<Point, double>();
        openSet.Enqueue(startNode, 0);

        var cameFrom = new Dictionary<Point, Point>();
        var gScore = new Dictionary<Point, double>();
        gScore[startNode] = 0;

        var fScore = new Dictionary<Point, double>();
        fScore[startNode] = Heuristic(startNode, endNode);

        while (openSet.Count > 0)
        {
            var current = openSet.Dequeue();

            if (current == endNode)
            {
                return ReconstructPath(cameFrom, current);
            }

            // 8방향 이동
            var neighbors = GetNeighbors(current);
            foreach (var neighbor in neighbors)
            {
                // 맵 밖이거나 장애물이면 스킵
                if (!IsValid(neighbor) || grid[neighbor.X, neighbor.Y])
                    continue;

                // 이동 비용 (직선 1, 대각선 1.414)
                double dist = (current.X == neighbor.X || current.Y == neighbor.Y) ? 1.0 : 1.414;
                double tentativeGScore = gScore[current] + dist;

                if (!gScore.ContainsKey(neighbor) || tentativeGScore < gScore[neighbor])
                {
                    cameFrom[neighbor] = current;
                    gScore[neighbor] = tentativeGScore;
                    double f = tentativeGScore + Heuristic(neighbor, endNode);
                    fScore[neighbor] = f;
                    
                    // PriorityQueue엔 Update 기능이 없으므로 중복 추가 (성능상 큰 문제 없음)
                    openSet.Enqueue(neighbor, f);
                }
            }
        }

        return new List<double[]>(); // 경로 없음
    }

    private List<double[]> ReconstructPath(Dictionary<Point, Point> cameFrom, Point current)
    {
        var totalPath = new List<double[]>();
        totalPath.Add(new double[] { current.X * GridSize + GridSize / 2, current.Y * GridSize + GridSize / 2 });

        while (cameFrom.ContainsKey(current))
        {
            current = cameFrom[current];
            totalPath.Add(new double[] { current.X * GridSize + GridSize / 2, current.Y * GridSize + GridSize / 2 });
        }

        totalPath.Reverse();
        return totalPath;
    }

    private List<Point> GetNeighbors(Point p)
    {
        return new List<Point>
        {
            new Point(p.X + 1, p.Y), new Point(p.X - 1, p.Y),
            new Point(p.X, p.Y + 1), new Point(p.X, p.Y - 1),
            new Point(p.X + 1, p.Y + 1), new Point(p.X - 1, p.Y - 1),
            new Point(p.X + 1, p.Y - 1), new Point(p.X - 1, p.Y + 1)
        };
    }

    private bool IsValid(Point p)
    {
        return p.X >= 0 && p.X < MapWidthCells && p.Y >= 0 && p.Y < MapHeightCells;
    }

    private double Heuristic(Point a, Point b)
    {
        // Euclidean distance
        return Math.Sqrt(Math.Pow(a.X - b.X, 2) + Math.Pow(a.Y - b.Y, 2));
    }

    private Point FindNearestWalkableNode(bool[,] grid, Point target)
    {
        // BFS로 가장 가까운 빈 공간 찾기
        var queue = new Queue<Point>();
        var visited = new HashSet<Point>();
        
        queue.Enqueue(target);
        visited.Add(target);

        while (queue.Count > 0)
        {
            var current = queue.Dequeue();
            
            if (IsValid(current) && !grid[current.X, current.Y])
            {
                return current;
            }

            foreach (var neighbor in GetNeighbors(current))
            {
                if (IsValid(neighbor) && !visited.Contains(neighbor))
                {
                    visited.Add(neighbor);
                    queue.Enqueue(neighbor);
                }
            }
        }
        
        return target; // 못 찾으면 원래 위치 반환 (결국 실패 처리됨)
    }
}
