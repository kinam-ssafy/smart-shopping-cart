namespace smart_shopping_cart_back.Models;

/// <summary>
/// 카트 위치 정보 DTO (MQTT에서 수신)
/// </summary>
public class CartPositionDto
{
    public double X { get; set; }
    public double Y { get; set; }
    public double Theta { get; set; }
    public double ThetaRad { get; set; }
    public CartPositionUncertainty? Uncertainty { get; set; }
    public double Timestamp { get; set; }
    public string? UpdatedAt { get; set; }
    public string? Time { get; set; }
}

public class CartPositionUncertainty
{
    public double X { get; set; }
    public double Y { get; set; }
}
