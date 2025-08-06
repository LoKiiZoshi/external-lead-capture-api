from rest_framework import generics, status, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Q, Avg, Count, Case, When, IntegerField
from django.db.models.functions import Round
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from datetime import timedelta
import uuid

from .models import Review, ItemReview, ReviewAnalytics
from .serializers import (
    ReviewCreateSerializer, ReviewListSerializer, ReviewUpdateSerializer,
    ItemReviewSerializer, ReviewAnalyticsSerializer,
    RestaurantReviewSummarySerializer, ReviewFilterSerializer
)


class ReviewCreateView(generics.CreateAPIView):
    """
    Create a new review with optional item reviews
    """
    queryset = Review.objects.all()
    serializer_class = ReviewCreateSerializer
    permission_classes = [AllowAny]
    
    def perform_create(self, serializer):
        """
        Save review and update analytics
        """
        review = serializer.save()
        self.update_restaurant_analytics(review.restaurant_id)
    
    def update_restaurant_analytics(self, restaurant_id):
        """
        Update or create analytics for the restaurant
        """
        try:
            reviews = Review.objects.filter(restaurant_id=restaurant_id)
            
            # Calculate aggregates
            analytics_data = reviews.aggregate(
                total_reviews=Count('id'),
                avg_overall=Avg('overall_rating'),
                avg_food=Avg('food_rating'),
                avg_service=Avg('service_rating'),
                avg_ambiance=Avg('ambiance_rating'),
                positive_count=Count(Case(
                    When(sentiment_score__gte=0.1, then=1),
                    output_field=IntegerField()
                )),
                neutral_count=Count(Case(
                    When(sentiment_score__lt=0.1, sentiment_score__gt=-0.1, then=1),
                    output_field=IntegerField()
                )),
                negative_count=Count(Case(
                    When(sentiment_score__lte=-0.1, then=1),
                    output_field=IntegerField()
                ))
            )
            
            # Update or create analytics
            analytics, created = ReviewAnalytics.objects.update_or_create(
                restaurant_id=restaurant_id,
                defaults={
                    'total_reviews': analytics_data['total_reviews'],
                    'average_overall_rating': Round(analytics_data['avg_overall'] or 0, 2),
                    'average_food_rating': Round(analytics_data['avg_food'] or 0, 2) if analytics_data['avg_food'] else None,
                    'average_service_rating': Round(analytics_data['avg_service'] or 0, 2) if analytics_data['avg_service'] else None,
                    'average_ambiance_rating': Round(analytics_data['avg_ambiance'] or 0, 2) if analytics_data['avg_ambiance'] else None,
                    'positive_sentiment_count': analytics_data['positive_count'],
                    'neutral_sentiment_count': analytics_data['neutral_count'],
                    'negative_sentiment_count': analytics_data['negative_count'],
                }
            )
        except Exception as e:
            print(f"Error updating analytics: {e}")


class ReviewListView(generics.ListAPIView):
    """
    List reviews with filtering and searching capabilities
    """
    queryset = Review.objects.all().prefetch_related('item_reviews')
    serializer_class = ReviewListSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['restaurant_id', 'overall_rating', 'is_anonymous']
    search_fields = ['comment']
    ordering_fields = ['created_at', 'overall_rating', 'sentiment_score']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """
        Filter queryset based on query parameters
        """
        queryset = super().get_queryset()
        
        # Custom filtering
        min_rating = self.request.query_params.get('min_rating')
        max_rating = self.request.query_params.get('max_rating')
        sentiment = self.request.query_params.get('sentiment')
        date_from = self.request.query_params.get('date_from')
        date_to = self.request.query_params.get('date_to')
        has_comment = self.request.query_params.get('has_comment')
        
        if min_rating:
            queryset = queryset.filter(overall_rating__gte=min_rating)
        
        if max_rating:
            queryset = queryset.filter(overall_rating__lte=max_rating)
        
        if sentiment:
            if sentiment == 'positive':
                queryset = queryset.filter(sentiment_score__gte=0.1)
            elif sentiment == 'negative':
                queryset = queryset.filter(sentiment_score__lte=-0.1)
            elif sentiment == 'neutral':
                queryset = queryset.filter(sentiment_score__lt=0.1, sentiment_score__gt=-0.1)
        
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        if has_comment is not None:
            if has_comment.lower() == 'true':
                queryset = queryset.exclude(Q(comment__isnull=True) | Q(comment=''))
            else:
                queryset = queryset.filter(Q(comment__isnull=True) | Q(comment=''))
        
        return queryset


class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete a specific review
    """
    queryset = Review.objects.all().prefetch_related('item_reviews')
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ReviewUpdateSerializer
        return ReviewListSerializer
    
    def perform_update(self, serializer):
        """
        Update review and refresh analytics
        """
        review = serializer.save()
        self.update_restaurant_analytics(review.restaurant_id)
    
    def perform_destroy(self, instance):
        """
        Delete review and refresh analytics
        """
        restaurant_id = instance.restaurant_id
        instance.delete()
        self.update_restaurant_analytics(restaurant_id)
    
    def update_restaurant_analytics(self, restaurant_id):
        """Same as in ReviewCreateView"""
        try:
            reviews = Review.objects.filter(restaurant_id=restaurant_id)
            
            if not reviews.exists():
                # Delete analytics if no reviews left
                ReviewAnalytics.objects.filter(restaurant_id=restaurant_id).delete()
                return
            
            analytics_data = reviews.aggregate(
                total_reviews=Count('id'),
                avg_overall=Avg('overall_rating'),
                avg_food=Avg('food_rating'),
                avg_service=Avg('service_rating'),
                avg_ambiance=Avg('ambiance_rating'),
                positive_count=Count(Case(
                    When(sentiment_score__gte=0.1, then=1),
                    output_field=IntegerField()
                )),
                neutral_count=Count(Case(
                    When(sentiment_score__lt=0.1, sentiment_score__gt=-0.1, then=1),
                    output_field=IntegerField()
                )),
                negative_count=Count(Case(
                    When(sentiment_score__lte=-0.1, then=1),
                    output_field=IntegerField()
                ))
            )
            
            ReviewAnalytics.objects.update_or_create(
                restaurant_id=restaurant_id,
                defaults={
                    'total_reviews': analytics_data['total_reviews'],
                    'average_overall_rating': Round(analytics_data['avg_overall'] or 0, 2),
                    'average_food_rating': Round(analytics_data['avg_food'] or 0, 2) if analytics_data['avg_food'] else None,
                    'average_service_rating': Round(analytics_data['avg_service'] or 0, 2) if analytics_data['avg_service'] else None,
                    'average_ambiance_rating': Round(analytics_data['avg_ambiance'] or 0, 2) if analytics_data['avg_ambiance'] else None,
                    'positive_sentiment_count': analytics_data['positive_count'],
                    'neutral_sentiment_count': analytics_data['neutral_count'],
                    'negative_sentiment_count': analytics_data['negative_count'],
                }
            )
        except Exception as e:
            print(f"Error updating analytics: {e}")


class ItemReviewListCreateView(generics.ListCreateAPIView):
    """
    List and create item reviews
    """
    serializer_class = ItemReviewSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        """
        Filter by review_id or menu_item_id if provided
        """
        queryset = ItemReview.objects.all()
        review_id = self.request.query_params.get('review_id')
        menu_item_id = self.request.query_params.get('menu_item_id')
        
        if review_id:
            queryset = queryset.filter(review_id=review_id)
        
        if menu_item_id:
            queryset = queryset.filter(menu_item_id=menu_item_id)
        
        return queryset.order_by('-created_at')


class RestaurantAnalyticsView(generics.RetrieveAPIView):
    """
    Get analytics for a specific restaurant
    """
    queryset = ReviewAnalytics.objects.all()
    serializer_class = ReviewAnalyticsSerializer
    permission_classes = [AllowAny]
    lookup_field = 'restaurant_id'


@api_view(['GET'])
@permission_classes([AllowAny])
def restaurant_review_summary(request, restaurant_id):
    """
    Get comprehensive review summary for a restaurant
    """
    try:
        # Validate restaurant_id
        uuid.UUID(restaurant_id)  # This will raise ValueError if invalid
        
        reviews = Review.objects.filter(restaurant_id=restaurant_id).prefetch_related('item_reviews')
        
        if not reviews.exists():
            return Response({
                'restaurant_id': restaurant_id,
                'total_reviews': 0,
                'average_overall_rating': 0,
                'rating_distribution': {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
                'recent_reviews': [],
                'top_rated_items': [],
                'sentiment_summary': {'positive': 0, 'neutral': 0, 'negative': 0}
            })
        
        # Basic stats
        total_reviews = reviews.count()
        average_rating = reviews.aggregate(avg=Avg('overall_rating'))['avg']
        
        # Rating distribution
        rating_dist = reviews.values('overall_rating').annotate(
            count=Count('overall_rating')
        ).order_by('overall_rating')
        rating_distribution = {i: 0 for i in range(1, 6)}
        for item in rating_dist:
            rating_distribution[item['overall_rating']] = item['count']
        
        # Recent reviews (last 10)
        recent_reviews = reviews.order_by('-created_at')[:10]
        recent_serializer = ReviewListSerializer(recent_reviews, many=True)
        
        # Top rated items
        top_items = ItemReview.objects.filter(
            review__restaurant_id=restaurant_id
        ).values('menu_item_id').annotate(
            avg_rating=Avg('rating'),
            review_count=Count('id')
        ).filter(review_count__gte=2).order_by('-avg_rating')[:5]
        
        # Sentiment summary
        sentiment_counts = reviews.aggregate(
            positive=Count(Case(When(sentiment_score__gte=0.1, then=1), output_field=IntegerField())),
            neutral=Count(Case(When(sentiment_score__lt=0.1, sentiment_score__gt=-0.1, then=1), output_field=IntegerField())),
            negative=Count(Case(When(sentiment_score__lte=-0.1, then=1), output_field=IntegerField()))
        )
        
        data = {
            'restaurant_id': restaurant_id,
            'total_reviews': total_reviews,
            'average_overall_rating': round(average_rating, 2) if average_rating else 0,
            'rating_distribution': rating_distribution,
            'recent_reviews': recent_serializer.data,
            'top_rated_items': list(top_items),
            'sentiment_summary': sentiment_counts
        }
        
        return Response(data)
        
    except ValueError:
        return Response(
            {'error': 'Invalid restaurant_id format'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def trending_restaurants(request):
    """
    Get trending restaurants based on recent positive reviews
    """
    try:
        # Get restaurants with reviews in the last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        trending = Review.objects.filter(
            created_at__gte=thirty_days_ago
        ).values('restaurant_id').annotate(
            recent_reviews=Count('id'),
            avg_rating=Avg('overall_rating'),
            positive_sentiment=Count(Case(
                When(sentiment_score__gte=0.1, then=1),
                output_field=IntegerField()
            ))
        ).filter(
            recent_reviews__gte=5,  # At least 5 reviews
            avg_rating__gte=4.0     # Average rating >= 4.0
        ).order_by('-positive_sentiment', '-avg_rating')[:10]
        
        return Response(list(trending))
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def batch_sentiment_analysis(request):
    """
    Run sentiment analysis on reviews that don't have sentiment scores
    """
    try:
        reviews_without_sentiment = Review.objects.filter(
            sentiment_score__isnull=True,
            comment__isnull=False
        ).exclude(comment='')
        
        updated_count = 0
        serializer = ReviewCreateSerializer()
        
        for review in reviews_without_sentiment:
            sentiment_score = serializer.analyze_sentiment(review.comment)
            if sentiment_score is not None:
                review.sentiment_score = sentiment_score
                review.save(update_fields=['sentiment_score'])
                updated_count += 1
        
        return Response({
            'message': f'Updated sentiment analysis for {updated_count} reviews',
            'updated_count': updated_count
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )