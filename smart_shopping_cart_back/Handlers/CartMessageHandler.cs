using smart_shopping_cart_back.Models;
using smart_shopping_cart_back.Services;
using System.Text.Json;

namespace smart_shopping_cart_back.Handlers;

/// <summary>
/// MQTT 메시지 처리 핸들러
/// - cart/1 토픽 메시지를 파싱
/// - SSE로 클라이언트에게 브로드캐스트
/// </summary>
public class CartMessageHandler
{
    private readonly ILogger<CartMessageHandler> _logger;

    public CartMessageHandler(ILogger<CartMessageHandler> logger)
    {
        _logger = logger;
    }

    /// <summary>
    /// MQTT 메시지 처리
    /// </summary>
    /// <param name="topic">수신된 토픽</param>
    /// <param name="payload">수신된 JSON 메시지</param>
    /// <param name="sse">SSE 서비스</param>
    public async Task HandleAsync(string topic, string payload, SseService sse)
    {
        try
        {
            // JSON 파싱
            var message = JsonSerializer.Deserialize<CartMessage>(payload);

            if (message?.Uids == null)
            {
                _logger.LogWarning($"[Handler] 유효하지 않은 메시지: {payload}");
                return;
            }

            _logger.LogInformation($"[Handler] UID 수신: {message.Uids.Length}개");

            // SSE로 UID 배열 브로드캐스트
            await sse.BroadcastUidsAsync(message.Uids);
        }
        catch (JsonException ex)
        {
            _logger.LogError($"[Handler] JSON 파싱 실패: {ex.Message}");
        }
    }
}
