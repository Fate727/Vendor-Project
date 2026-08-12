from django.utils import timezone
from SellerModule.models import Product
from UserModule.models import ProductAnalytics
from .predict import predict_stock


def get_seller_recommendations(seller, search=""):
    recommendations = []
    
    analytics = (
        ProductAnalytics.objects
        .filter(SellerID=seller)
        .select_related("ProductID", "ProductID__Category")
        .order_by("-TotalSales")
    )
    
    if search:
        analytics = analytics.filter(ProductID__ProductName__icontains=search)
    
    today = timezone.now()
    
    for item in analytics:
        product = item.ProductID
        
        try:
            features = {
                "ProductID": product.ProductID,
                "SellerID": seller.SellerID,
                "TotalSales": item.TotalSales,
                "SalesLast7Days": item.SalesLast7Days,
                "SalesPrevious7Days": item.SalesPrevious7Days,
                "SalesLast30Days": item.SalesLast30Days,
                "SalesGrowthRate": item.SalesGrowthRate,
                "Revenue": float(item.Revenue),
                "AvgDailySales": item.AvgSalesPerDay,
                "Price": float(item.Price),
                "CategoryID": (
                    product.Category.category_id
                    if product.Category
                    else 0
                ),
                "CurrentStock": product.Stock,
                "ProductAgeDays": (
                    today.date() - product.CreatedAt.date()
                ).days,
                "DaysSinceLastSale": item.DaysSinceLastSale,
                "Year": today.year,
                "Month": today.month,
                "Week": today.isocalendar().week,
                "Day": today.day,
                "DayOfWeek": today.weekday(),
            }
            
            prediction = predict_stock(features)
            
        except Exception as e:
            print(f"Prediction failed for {product.ProductName}: {e}")
            prediction = 0
        
        
        if prediction > 0:
            recommendation = "Increase Stock"
            increase_by = prediction
            reduce_by = 0
        elif prediction < 0:
            recommendation = "Reduce Stock"
            increase_by = 0
            reduce_by = abs(prediction)
        else:
            recommendation = "Keep Current Stock"
            increase_by = 0
            reduce_by = 0
        
        recommendations.append({
            "product": product,
            "analytics": item,
            "prediction": prediction,
            "recommendation": recommendation,
            "increase_by": increase_by,
            "reduce_by": reduce_by,
        })
    
    return recommendations