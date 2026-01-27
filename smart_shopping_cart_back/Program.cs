using smart_shopping_cart_back.Services;

var builder = WebApplication.CreateBuilder(args);

// ===== 서비스 등록 =====

// 컨트롤러 서비스 추가 (Controllers 폴더의 API 컨트롤러들을 자동 인식)
builder.Services.AddControllers();

// CORS 설정 (Cross-Origin Resource Sharing)
// - 프론트엔드에서 이 백엔드 API를 호출할 수 있도록 허용
builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy =>
    {
        policy.AllowAnyOrigin()   // 모든 출처 허용
              .AllowAnyMethod()   // 모든 HTTP 메서드 허용 (GET, POST 등)
              .AllowAnyHeader();  // 모든 헤더 허용
    });
});

// MQTT 서비스 등록 (Singleton: 앱 전체에서 하나의 인스턴스만 사용)
builder.Services.AddSingleton<MqttService>();

// ===== 앱 빌드 =====
var app = builder.Build();

// ===== 미들웨어 설정 =====

// CORS 미들웨어 활성화
app.UseCors();

// 컨트롤러 라우팅 매핑
// - Controllers 폴더의 API 컨트롤러들을 자동으로 라우팅
app.MapControllers();

// ===== 서버 실행 =====
app.Run();
