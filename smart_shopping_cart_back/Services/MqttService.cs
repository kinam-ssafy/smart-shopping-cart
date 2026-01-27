using MQTTnet;
using MQTTnet.Client;
using System.Text;

namespace smart_shopping_cart_back.Services;

/// <summary>
/// MQTT 브로커와 통신하는 서비스 클래스
/// - MQTT 브로커에 연결/연결해제
/// - 토픽 구독 및 메시지 수신
/// - 특정 토픽에 메시지 발행
/// </summary>
public class MqttService
{
    // MQTT 클라이언트 인스턴스 (null일 수 있음)
    private IMqttClient? _client;
    
    // appsettings.json에서 설정을 읽기 위한 IConfiguration
    private readonly IConfiguration _config;

    /// <summary>
    /// MQTT 브로커 연결 상태 확인
    /// - true: 연결됨
    /// - false: 연결 안됨
    /// </summary>
    public bool IsConnected => _client?.IsConnected ?? false;

    /// <summary>
    /// 생성자 - DI를 통해 IConfiguration 주입받음
    /// </summary>
    /// <param name="config">appsettings.json 설정 객체</param>
    public MqttService(IConfiguration config)
    {
        _config = config;
    }

    /// <summary>
    /// MQTT 브로커에 연결
    /// - appsettings.json에서 Broker 주소와 Port를 읽어서 연결
    /// </summary>
    public async Task ConnectAsync()
    {
        // MQTT 클라이언트 팩토리로 클라이언트 생성
        var factory = new MqttClientFactory();
        _client = factory.CreateMqttClient();

        // appsettings.json에서 브로커 설정 읽기
        // 기본값: localhost:1883
        var broker = _config["Mqtt:Broker"] ?? "localhost";
        var port = int.Parse(_config["Mqtt:Port"] ?? "1883");

        // 연결 옵션 설정
        var options = new MqttClientOptionsBuilder()
            .WithTcpServer(broker, port)           // 브로커 주소와 포트
            .WithClientId($"smart-cart-{Guid.NewGuid()}")  // 고유 클라이언트 ID
            .Build();

        // 브로커에 연결
        await _client.ConnectAsync(options);
    }

    /// <summary>
    /// MQTT 브로커 연결 해제
    /// </summary>
    public async Task DisconnectAsync()
    {
        // 클라이언트가 있고 연결된 상태일 때만 연결 해제
        if (_client != null && _client.IsConnected)
            await _client.DisconnectAsync();
    }

    /// <summary>
    /// 특정 토픽 구독 및 메시지 수신 시 콜백 실행
    /// </summary>
    /// <param name="topic">구독할 토픽 (예: "cart/#")</param>
    /// <param name="onMessage">메시지 수신 시 실행할 콜백 함수 (topic, payload)</param>
    public async Task SubscribeAsync(string topic, Action<string, string> onMessage)
    {
        if (_client == null) return;

        // 메시지 수신 이벤트 핸들러 등록
        _client.ApplicationMessageReceivedAsync += e =>
        {
            // 수신한 토픽
            var t = e.ApplicationMessage.Topic;
            // 수신한 메시지 (바이트 배열 -> 문자열 변환)
            var p = Encoding.UTF8.GetString(e.ApplicationMessage.PayloadSegment);
            // 콜백 함수 호출
            onMessage(t, p);
            return Task.CompletedTask;
        };

        // 토픽 구독
        await _client.SubscribeAsync(topic);
    }

    /// <summary>
    /// 특정 토픽에 메시지 발행
    /// </summary>
    /// <param name="topic">발행할 토픽 (예: "cart/location")</param>
    /// <param name="message">발행할 메시지 내용</param>
    public async Task PublishAsync(string topic, string message)
    {
        // 클라이언트가 없거나 연결 안됐으면 무시
        if (_client == null || !_client.IsConnected) return;

        // 발행할 메시지 생성
        var msg = new MqttApplicationMessageBuilder()
            .WithTopic(topic)
            .WithPayload(message)
            .Build();

        // 메시지 발행
        await _client.PublishAsync(msg);
    }
}
