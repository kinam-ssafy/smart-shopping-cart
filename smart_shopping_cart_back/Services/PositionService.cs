using System.Text.Json;
using smart_shopping_cart_back.Models;

namespace smart_shopping_cart_back.Services;

/// <summary>
/// 카트 위치 처리 서비스
/// - MQTT 메시지 파싱
/// - 쓰로틀링 적용 (150ms 간격)
/// - 위치 변경 이벤트 발생
/// </summary>
public class PositionService
{
    private readonly ILogger<PositionService> _logger;
    private CartPositionDto? _currentPosition;
    private readonly object _lock = new();

    // 쓰로틀링 설정 (150ms = 약 6-7 FPS)
    private DateTime _lastBroadcast = DateTime.MinValue;
    private readonly TimeSpan _throttleInterval = TimeSpan.FromMilliseconds(150);

    /// <summary>
    /// 위치 업데이트 이벤트 (쓰로틀링 적용됨)
    /// </summary>
    public event Action<CartPositionDto>? OnPositionUpdated;

    /// <summary>
    /// 현재 위치 조회
    /// </summary>
    public CartPositionDto? CurrentPosition
    {
        get { lock (_lock) return _currentPosition; }
    }

    public PositionService(ILogger<PositionService> logger)
    {
        _logger = logger;
    }

    /// <summary>
    /// MQTT 메시지 처리 (cart/1/position)
    /// </summary>
    public void HandlePositionMessage(string payload)
    {
        try
        {
            var options = new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true,
                PropertyNamingPolicy = JsonNamingPolicy.SnakeCaseLower
            };

            var position = JsonSerializer.Deserialize<CartPositionDto>(payload, options);

            if (position != null)
            {
                // 항상 최신 위치 저장
                lock (_lock)
                {
                    _currentPosition = position;
                }

                // 쓰로틀링: 일정 간격으로만 브로드캐스트
                var now = DateTime.UtcNow;
                if (now - _lastBroadcast >= _throttleInterval)
                {
                    _lastBroadcast = now;
                    _logger.LogDebug($"[Position] 브로드캐스트: x={position.X:F3}, y={position.Y:F3}, theta={position.Theta:F1}°");
                    OnPositionUpdated?.Invoke(position);
                }
            }
        }
        catch (JsonException ex)
        {
            _logger.LogWarning($"[Position] 파싱 실패: {ex.Message}");
        }
    }
}
