import json
import uuid

from django.http import JsonResponse
# from yookassa import Configuration, Payment
from django.conf import settings
from cart.cart import Cart
from .models import Order, OrderItem


def start_order(request):
    cart = Cart(request)
    data = json.loads(request.body)
    total_price = 0

    order_num = request.user.orders

    print(order_num)

    items = []

    for item in cart:
        product = item['product']
        total_price += product.price * int(item['quantity'])

        items.append({
            'name': product.name,
            'unit_amount': product.price,
            'quantity': item['quantity']
        })

    payment_method = data['payment_method']

    Configuration.account_id = settings.YOOKASSA_ACCOUNT_ID
    Configuration.secret_key = settings.YOOKASSA_SECRET_KEY

    idempotence_key = str(uuid.uuid4())

    payment = Payment.create(
        {
            "amount": {
                "value": total_price,
                "currency": "RUB"
            },
            "payment_method_data": {
                "type": payment_method,
                "phone": data['phone']
            },
            "confirmation": {
                "type": "redirect",
                "return_url": "http://127.0.0.1:8000/myaccount/"
            },
            "description": order_num
        }, idempotence_key)

    # get confirmation url
    confirmation_url = payment.confirmation.confirmation_url
    payment_id = payment.id

    order = Order.objects.create(
        user=request.user,
        first_name=data['first_name'],
        last_name=data['last_name'],
        email=data['email'],
        phone=data['phone'],
        address=data['address'],
        zipcode=data['zipcode'],
        place=data['place'],
        payment_id=payment_id,
        paid_amount=total_price
    )
    order.save()

    for item in cart:
        product = item['product']
        quantity = int(item['quantity'])
        price = product.price * quantity

        item = OrderItem.objects.create(order=order, product=product, price=price, quantity=quantity)
        item.save()

    cart.clear()

    return JsonResponse({'confirmation_url': confirmation_url, 'order': payment_id})