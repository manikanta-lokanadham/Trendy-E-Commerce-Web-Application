from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from products.models import Product
from .models import WishlistItem

@login_required
def toggle_wishlist(request, product_id):
    if request.method == 'POST':
        try:
            product = Product.objects.get(id=product_id)
            wishlist_item = WishlistItem.objects.filter(user=request.user, product=product)
            
            if wishlist_item.exists():
                wishlist_item.delete()
                is_in_wishlist = False
            else:
                WishlistItem.objects.create(user=request.user, product=product)
                is_in_wishlist = True
            
            return JsonResponse({
                'success': True,
                'is_in_wishlist': is_in_wishlist,
                'wishlist_count': WishlistItem.objects.filter(user=request.user).count()
            })
        except Product.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Product not found'
            }, status=404)
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request'
    }, status=400) 