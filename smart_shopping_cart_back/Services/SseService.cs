using System.Collections.Concurrent;
using System.Text.Json;
using System.Text.Json.Serialization;
using smart_shopping_cart_back.Models;

namespace smart_shopping_cart_back.Services;

/// <summary>
/// SSE(Server-Sent Events) 서비스
/// - SSE 연결 관리
/// - MQTT 메시지를 SSE로 브로드캐스트
/// </summary>
public class SseService
{
    private readonly ConcurrentDictionary<string, HttpResponse> _clients = new();
    private readonly ILogger<SseService> _logger;
    private readonly JsonSerializerOptions _jsonOptions;

    public SseService(ILogger<SseService> logger)
    {
        _logger = logger;
        _jsonOptions = new JsonSerializerOptions
        {
            PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
            DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull
        };
    }

    /// <summary>
    /// 새 SSE 클라이언트 등록
    /// </summary>
    public string AddClient(HttpResponse response)
    {
        var clientId = Guid.NewGuid().ToString();
        _clients.TryAdd(clientId, response);
        _logger.LogInformation($"[SSE] 클라이언트 연결: {clientId} (총 {_clients.Count}명)");
        return clientId;
    }

    /// <summary>
    /// SSE 클라이언트 제거
    /// </summary>
    public void RemoveClient(string clientId)
    {
        _clients.TryRemove(clientId, out _);
        _logger.LogInformation($"[SSE] 클라이언트 해제: {clientId} (총 {_clients.Count}명)");
    }

    /// <summary>
    /// 특정 클라이언트에게 상품 목록 전송 (초기 연결 시)
    /// </summary>
    public async Task SendToClientAsync(HttpResponse response, List<CartProductDto> products)
    {
        try
        {
            var data = JsonSerializer.Serialize(new { products }, _jsonOptions);
            var message = $"data: {data}\n\n";
            await response.WriteAsync(message);
            await response.Body.FlushAsync();
        }
        catch (Exception ex)
        {
            _logger.LogError($"[SSE] 전송 실패: {ex.Message}");
        }
    }

    /// <summary>
    /// 모든 SSE 클라이언트에게 상품 목록 전송
    /// </summary>
    public async Task BroadcastProductsAsync(List<CartProductDto> products)
    {
        var data = JsonSerializer.Serialize(new { products }, _jsonOptions);
        var message = $"data: {data}\n\n";

        foreach (var (clientId, response) in _clients)
        {
            try
            {
                await response.WriteAsync(message);
                await response.Body.FlushAsync();
            }
            catch (Exception)
            {
                RemoveClient(clientId);
            }
        }

        _logger.LogInformation($"[SSE] 브로드캐스트: {products.Count}개 상품 → {_clients.Count}명");
    }

    /// <summary>
    /// 모든 SSE 클라이언트에게 UID 배열 전송 (레거시 호환)
    /// </summary>
    public async Task BroadcastUidsAsync(string[] uids)
    {
        var data = JsonSerializer.Serialize(new { uids }, _jsonOptions);
        var message = $"data: {data}\n\n";

        foreach (var (clientId, response) in _clients)
        {
            try
            {
                await response.WriteAsync(message);
                await response.Body.FlushAsync();
            }
            catch (Exception)
            {
                RemoveClient(clientId);
            }
        }
    }
}
