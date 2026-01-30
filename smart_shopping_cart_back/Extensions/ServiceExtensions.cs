using smart_shopping_cart_back.BackgroundServices;
using smart_shopping_cart_back.Handlers;
using smart_shopping_cart_back.Services;

namespace smart_shopping_cart_back.Extensions;

/// <summary>
/// 서비스 등록 확장 메서드
/// - Program.cs를 깔끔하게 유지하기 위해 DI 등록을 여기에 모아놓음
/// </summary>
public static class ServiceExtensions
{
    /// <summary>
    /// MQTT 관련 서비스 등록
    /// </summary>
    public static IServiceCollection AddMqttServices(this IServiceCollection services)
    {
        // CartDbService: 카트 DB 서비스 (Singleton)
        services.AddSingleton<CartDbService>();

        // MqttService: MQTT 브로커 통신 (Singleton)
        services.AddSingleton<MqttService>();

        // PositionService: 위치 데이터 처리 (Singleton)
        services.AddSingleton<PositionService>();

        // CartMessageHandler: MQTT 메시지 처리 (Singleton)
        services.AddSingleton<CartMessageHandler>();

        // MqttHostedService: 백그라운드에서 MQTT 연결 관리
        services.AddHostedService<MqttHostedService>();

        return services;
    }

    /// <summary>
    /// SSE 관련 서비스 등록
    /// </summary>
    public static IServiceCollection AddSseServices(this IServiceCollection services)
    {
        // SseService: SSE 클라이언트 관리 (Singleton)
        services.AddSingleton<SseService>();

        return services;
    }

    /// <summary>
    /// CORS 설정
    /// </summary>
    public static IServiceCollection AddCorsPolicy(this IServiceCollection services)
    {
        services.AddCors(options =>
        {
            options.AddDefaultPolicy(policy =>
            {
                policy.AllowAnyOrigin()
                      .AllowAnyMethod()
                      .AllowAnyHeader();
            });
        });

        return services;
    }
}
