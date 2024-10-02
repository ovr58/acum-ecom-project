import time
from django.conf import settings

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from product.models import Product, Category
from django.db.models import Q
from django.core.paginator import Paginator

from .forms import SignUpForm
import requests
import json
from transliterate import translit


def frontpage(request):
    products = Product.objects.all()[0:8]

    return render(request, 'core/frontpage.html', {'products': products})


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)

        if form.is_valid():
            user = form.save()

            login(request, user)

            return redirect('/')
    else:
        form = SignUpForm()
    return render(request, 'core/signup.html', {'form': form})


@login_required
def myaccount(request):
    return render(request, 'core/myaccount.html')


@login_required
def edit_myaccount(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        user.save()

        return redirect('myaccount')
    return render(request, 'core/edit_myaccount.html')


def shop(request):
    categories = Category.objects.all()
    products = Product.objects.all()

    active_category = request.GET.get('category', '')

    query = request.GET.get('query', '')

    if query:
        products = search_for_existed(query)

    if active_category:
        products = products.filter(category__slug=active_category)

    count = 20
    p = Paginator(products, count)
    if request.GET.get('page'):
        page_we_on = int(request.GET.get('page'))
    else:
        page_we_on = 1

    venues = p.get_page(page_we_on)
    nums = venues.paginator.num_pages
    list_nums = []

    if nums >= 2:
        for list_num in range(1, nums + 1):
            if (nums - 3) > list_num > 3:
                if list_num == (page_we_on - 1) or list_num == (page_we_on + 1):
                    list_nums.append(str(list_num))
                elif list_num == (page_we_on - 2) or list_num == (page_we_on + 2):
                    list_nums.append('...')
                elif list_num == page_we_on:
                    list_nums.append(str(list_num))
                else:
                    list_nums.append('?')
            else:
                list_nums.append(str(list_num))

    context = {
        'categories': categories,
        'products': products,
        'active_category': active_category,
        'count': count,
        'venues': venues,
        'list_nums': list_nums
    }

    return render(request, 'core/shop.html', context)


def learn_we_dont_have(query):
    response_auth = "https://api.v-avto.ru/v1/search/name.json?key=" + settings.API_KEY + "&q=" + query
    response_catalog = "https://api.v-avto.ru/v1/catalogs.json?key=" + settings.API_KEY

    # insert check if not error respose
    departments = requests.get(response_catalog)
    departments = json.loads(departments.text)
    departments = departments['response']['catalogs']
    v_response = requests.get(response_auth)
    v_response = json.loads(v_response.text)

    for page in range(1, int(v_response['response']['page']['pages'])):

        time.sleep(0.3)
        if page > 1:
            response_auth = "https://api.v-avto.ru/v1/search/name.json?key=" + settings.API_KEY + "&page=" + \
                            str(page) + "&q=" + query
            v_response = requests.get(response_auth)
            v_response = json.loads(v_response.text)

        v_products = v_response['response']['items']
        v_departments = v_response['response']['departments']

        for v_category in v_departments:
            if v_category != '1 Все Подразделения':
                category_new = Category.objects.update_or_create(
                    name=v_category,
                    slug=translit(v_category, "ru", reversed=True),
                    defaults={'name': v_category},
                )

        for v_product in v_products:
            pass
            # sub_index = next((d for (i, d) in enumerate(departments) if d['va_catalog_id'] == v_product['va_catalog_id']))
            #
            # catalog_index = next(
            #     (d for (i, d) in enumerate(departments) if d['va_catalog_id'] == sub_index['va_parent_id']))
            #
            # category_new = Category.objects.update_or_create(
            #     name=catalog_index['name'],
            #     slug=translit(catalog_index['name'], "ru", reversed=True),
            #     defaults={'name': catalog_index['name']},
            # )
            #
            # category = Category.objects.get(name=catalog_index['name'])
            #
            # url = v_product['images'][0] if len(v_product['images']) > 0 else 'https://via.placeholder.com/240x240x.jpg'
            # img_name = Path(urlparse(url).path).name
            # product_item = Product.objects.update_or_create(
            #     category=category,
            #     name=v_product['name'],
            #     mog=v_product['mog'],
            #     slug=translit(v_product['mog'], "ru", reversed=True),
            #     price=v_product['price'],
            #     description=v_product['name'] + ' .' + 'Производитель: ' + v_product['oem_brand'] + ' .' +
            #                 v_product['unit'] + '. ' + 'Наличие: ' + str(v_product['count']) +
            #                 v_product['unit'] + '.',
            #     created_at=datetime.today().strftime('%Y-%m-%d %H:%M:%S'),
            # )
            # product_item = Product.objects.get(mog=v_product['mog'])
            # with requests.get(url, stream=True) as r:
            #     r.raw.seek = lambda x: 0
            #     r.raw.size = int(r.headers["Content-Length"])
            #     product_item.image.save(img_name, r.raw, save=True)

    categories = Category.objects.all()
    products = Product.objects.all

    return products, categories


def search_for_existed(query):
    search_query = Q()

    for product_item in Product.objects.all():
        if product_item.name.lower().find(query) > 0:
            search_query |= Q(slug__startswith=product_item.slug)

    if search_query == Q():
        pass

    return Product.objects.filter(search_query)