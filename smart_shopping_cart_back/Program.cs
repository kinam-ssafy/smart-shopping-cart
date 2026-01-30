using smart_shopping_cart_back.Extensions;
using smart_shopping_cart_back.Services;
using smart_shopping_cart_back.Data;

var builder = WebApplication.CreateBuilder(args);

// ===== 서비스 등록 =====
builder.Services.AddControllers();
builder.Services.AddCorsPolicy();      // CORS 설정
builder.Services.AddMqttServices();    // MQTT 서비스 + 백그라운드 서비스
builder.Services.AddSseServices();     // SSE 서비스
builder.Services.AddSearchServices();  // 검색 서비스

builder.Services.AddDbContext<AppDbContext>();

var app = builder.Build();

// ===== 미들웨어 =====
app.UseCors();
app.MapControllers();

// ===== 서버 실행 =====
app.Run();
