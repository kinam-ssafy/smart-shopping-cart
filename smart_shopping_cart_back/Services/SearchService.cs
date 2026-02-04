using Microsoft.EntityFrameworkCore;
using smart_shopping_cart_back.Data;
using smart_shopping_cart_back.Models;
using smart_shopping_cart_back.Repositories;
using smart_shopping_cart_back.Services;

namespace smart_shopping_cart_back.Services;

public class SearchService : ISearchService
{
    private readonly AppDbContext _db;
    private readonly ICartRepository _cartRepository;
    private readonly IEmbeddingService _embeddingService;
    private readonly IRecommendationRepository _recommendationRepository;
    private readonly ISeasonalContextRepository _seasonalContextRepository;

    public SearchService(
        AppDbContext db,
        ICartRepository cartRepository,
        IEmbeddingService embeddingService,
        IRecommendationRepository recommendationRepository,
        ISeasonalContextRepository seasonalContextRepository)
    {
        _db = db;
        _cartRepository = cartRepository;
        _embeddingService = embeddingService;
        _recommendationRepository = recommendationRepository;
        _seasonalContextRepository = seasonalContextRepository;
    }

    public async Task<List<ProductDto>> SearchByNameAsync(string query, CancellationToken ct)
    {
        // Simple search example
        var ids = await _db.Products
            .AsNoTracking()
            .Where(p => p.Active && EF.Functions.ILike(p.Name, $"%{query}%"))
            .Select(p => p.ProductId)
            .ToListAsync(ct);

        return await CardQueryService.BuildCardsAsync(_db, ids, ct);
    }

    public async Task<SearchDefaultResponseDto> SearchDefaultAsync(CancellationToken ct)
    {
        const int TOP_K = 6;

        var popularIds = await _db.Products
            .AsNoTracking()
            .Where(p => p.Active)
            .Select(p => new
            {
                p.ProductId,
                Avg = _db.Reviews
                    .Where(r => r.ProductId == p.ProductId)
                    .Select(r => (double?)r.Rating)
                    .Average() ?? 0.0,
                Cnt = _db.Reviews.Count(r => r.ProductId == p.ProductId)
            })
            .OrderByDescending(x => x.Avg)
            .ThenByDescending(x => x.Cnt)
        .ThenBy(x => x.ProductId)
        .Take(TOP_K)
        .Select(x => x.ProductId)
        .ToListAsync(ct);

        List<long> recommendedIds;

        var cart = await _cartRepository.GetActiveCartAsync(ct);
        var cartProductIds = cart != null
            ? await _cartRepository.GetProductIdsAsync(cart.CartId, ct)
            : new List<long>();

        if (cartProductIds.Count > 0)
        {
            var cartProductNames = await _db.Products
                .AsNoTracking()
                .Where(p => cartProductIds.Contains(p.ProductId))
                .Select(p => p.Name)
                .ToListAsync(ct);

            var contextText = string.Join(", ", cartProductNames);

            var queryVector = await _embeddingService.EmbedAsync(contextText, ct);

            recommendedIds = await _recommendationRepository
                .FindRecommendedProductIdsAsync(
                    queryVector,
                    excludeProductIds: cartProductIds,
                    topK: TOP_K,
                    ct
                );
        }
        else
        // Cart is empty: Use seasonal RAG to find pool, then randomly circulate
        {
            const int SEASONAL_POOL_N = 30;
            
            var excludeNow = new HashSet<long>();

            foreach (var id in popularIds)
            {
                excludeNow.Add(id);
            }
            
            var season = GetCurrentSeason();
            var queryVector = await _seasonalContextRepository.GetSeasonalEmbeddingAsync(season, ct);
            
            if (queryVector == null)
            {
                // Fallback to empty list if season not found
                recommendedIds = new List<long>();
                goto afterRecommendations;
            }

            var seasonalPoolIds = await _recommendationRepository
                .FindRecommendedProductIdsAsync(
                    queryVector,
                    excludeProductIds: excludeNow.ToList(),
                    topK: SEASONAL_POOL_N,
                    ct
                );
            
            recommendedIds = seasonalPoolIds
                .OrderBy(_ => Random.Shared.Next())
                .Take(TOP_K)
                .ToList();
        }

        afterRecommendations:
        var popular = await CardQueryService.BuildCardsAsync(_db, popularIds, ct);
        var recommended = await CardQueryService.BuildCardsAsync(_db, recommendedIds, ct);

        return new SearchDefaultResponseDto(popular, recommended);
    }

    private string GetCurrentSeason()
    {
        var currentMonth = DateTime.Now.Month;
        
        return currentMonth switch
        {
            12 or 1 or 2 => "winter",
            3 or 4 or 5 => "spring",
            6 or 7 or 8 => "summer",
            9 or 10 or 11 => "autumn",
            _ => "winter"
        };
    }
}
