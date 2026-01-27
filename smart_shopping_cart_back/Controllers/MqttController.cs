using Microsoft.AspNetCore.Mvc;
using smart_shopping_cart_back.Services;

namespace smart_shopping_cart_back.Controllers;

/// <summary>
/// MQTT 관련 API 컨트롤러
/// - 브로커 연결/해제
/// - 메시지 발행
/// - 연결 상태 확인
/// </summary>
[ApiController]
[Route("api/[controller]")]  // → /api/mqtt
public class MqttController : ControllerBase
{
    // MQTT 서비스 (DI로 주입받음)
    private readonly MqttService _mqtt;

    /// <summary>
    /// 생성자 - DI를 통해 MqttService 주입받음
    /// </summary>
    public MqttController(MqttService mqtt)
    {
        _mqtt = mqtt;
    }

    /// <summary>
    /// MQTT 연결 상태 확인
    /// GET /api/mqtt/status
    /// </summary>
    [HttpGet("status")]
    public IActionResult GetStatus()
    {
        return Ok(new
        {
            connected = _mqtt.IsConnected,
            timestamp = DateTime.UtcNow
        });
    }

    /// <summary>
    /// MQTT 브로커에 연결
    /// POST /api/mqtt/connect
    /// </summary>
    [HttpPost("connect")]
    public async Task<IActionResult> Connect()
    {
        await _mqtt.ConnectAsync();
        return Ok(new { message = "MQTT 브로커에 연결되었습니다" });
    }

    /// <summary>
    /// MQTT 브로커 연결 해제
    /// POST /api/mqtt/disconnect
    /// </summary>
    [HttpPost("disconnect")]
    public async Task<IActionResult> Disconnect()
    {
        await _mqtt.DisconnectAsync();
        return Ok(new { message = "MQTT 브로커 연결이 해제되었습니다" });
    }

    /// <summary>
    /// 특정 토픽에 메시지 발행
    /// POST /api/mqtt/publish
    /// Body: { "topic": "cart/test", "message": "hello" }
    /// </summary>
    [HttpPost("publish")]
    public async Task<IActionResult> Publish([FromBody] PublishRequest req)
    {
        await _mqtt.PublishAsync(req.Topic, req.Message);
        return Ok(new { message = $"'{req.Topic}' 토픽에 메시지를 발행했습니다" });
    }
}

/// <summary>
/// 메시지 발행 요청 객체
/// </summary>
public class PublishRequest
{
    /// <summary>발행할 토픽 (예: "cart/location")</summary>
    public string Topic { get; set; } = "";
    
    /// <summary>발행할 메시지 내용</summary>
    public string Message { get; set; } = "";
}
