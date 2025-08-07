from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# URL patterns for the Review and Rating app
urlpatterns = [
    # Review endpoints
    path('reviews/', views.ReviewListView.as_view(), name='review-list'),
    path('reviews/create/', views.ReviewCreateView.as_view(), name='review-create'),
    path('reviews/<uuid:pk>/', views.ReviewDetailView.as_view(), name='review-detail'),
    
    # Item review endpoints
    path('item-reviews/', views.ItemReviewListCreateView.as_view(), name='item-review-list-create'),
    
    # Restaurant analytics and summary endpoints
    path('restaurants/<uuid:restaurant_id>/analytics/', views.RestaurantAnalyticsView.as_view(), name='restaurant-analytics'),
    path('restaurants/<uuid:restaurant_id>/summary/', views.restaurant_review_summary, name='restaurant-summary'),
    
    # Utility endpoints
    path('trending-restaurants/', views.trending_restaurants, name='trending-restaurants'),
    path('batch-sentiment-analysis/', views.batch_sentiment_analysis, name='batch-sentiment-analysis'),
]

# Alternative URL patterns with more RESTful structure
restful_urlpatterns = [
    # Review CRUD operations
    path('api/v1/reviews/', views.ReviewListView.as_view(), name='api-review-list'),
    path('api/v1/reviews/create/', views.ReviewCreateView.as_view(), name='api-review-create'),
    path('api/v1/reviews/<uuid:pk>/', views.ReviewDetailView.as_view(), name='api-review-detail'),
    path('api/v1/reviews/<uuid:pk>/update/', views.ReviewDetailView.as_view(), name='api-review-update'),
    path('api/v1/reviews/<uuid:pk>/delete/', views.ReviewDetailView.as_view(), name='api-review-delete'),
    
    # Item reviews
    path('api/v1/item-reviews/', views.ItemReviewListCreateView.as_view(), name='api-item-review-list'),
    path('api/v1/item-reviews/create/', views.ItemReviewListCreateView.as_view(), name='api-item-review-create'),
    
    # Restaurant-specific endpoints
    path('api/v1/restaurants/<uuid:restaurant_id>/reviews/', views.ReviewListView.as_view(), name='api-restaurant-reviews'),
    path('api/v1/restaurants/<uuid:restaurant_id>/analytics/', views.RestaurantAnalyticsView.as_view(), name='api-restaurant-analytics'),
    path('api/v1/restaurants/<uuid:restaurant_id>/summary/', views.restaurant_review_summary, name='api-restaurant-summary'),
    
    # Analytics and reporting
    path('api/v1/analytics/trending-restaurants/', views.trending_restaurants, name='api-trending-restaurants'),
    path('api/v1/analytics/sentiment-analysis/', views.batch_sentiment_analysis, name='api-batch-sentiment'),
]

# You can use either urlpatterns or restful_urlpatterns depending on your preference
# For main app urls.py, include like this:
# path('reviews/', include('reviews.urls')),