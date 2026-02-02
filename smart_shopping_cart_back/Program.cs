using smart_shopping_cart_back.Extensions;
using smart_shopping_cart_back.Services;
using smart_shopping_cart_back.Data;
using Microsoft.EntityFrameworkCore;

var builder = WebApplication.CreateBuilder(args);

// ===== 서비스 등록 =====
builder.Services.AddControllers();
builder.Services.AddCorsPolicy();      // CORS 설정
// builder.Services.AddMqttServices();    // MQTT 서비스 + 백그라운드 서비스
builder.Services.AddSseServices();     // SSE 서비스
builder.Services.AddSearchServices();  // 검색 서비스

builder.Services.AddHttpClient(); // general purpose

builder.Services.AddScoped<IEmbeddingService, EmbeddingService>();
builder.Services.AddScoped<IRecommendationRepository, RecommendationRepository>();


// DB & Repository
builder.Services.AddDbContext<AppDbContext>(options =>
    options.UseNpgsql(builder.Configuration.GetConnectionString("DefaultConnection"),
        o => o.UseVector()));
builder.Services.AddScoped<smart_shopping_cart_back.Repositories.ICartRepository, smart_shopping_cart_back.Repositories.CartRepository>();

// Map Service
builder.Services.AddSingleton<MapService>();
builder.Services.AddSingleton<NavigationService>();

var app = builder.Build();

// ===== 미들웨어 =====
app.UseCors();
app.MapControllers();

// ===== 서버 실행 =====
app.Run();
