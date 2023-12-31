import datetime
import json
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from django.core import serializers

from django.shortcuts import render
from django.http import HttpResponseRedirect
from main.forms import ProductForm
from django.urls import reverse

from main.models import Product

from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages  
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

from django.db.models import Sum

from django.views.decorators.csrf import csrf_exempt

# Create your views here.
@login_required(login_url='/login')
def show_main(request):
    products = Product.objects.filter(user=request.user)
    total_stock = products.aggregate(Sum('amount'))['amount__sum'] or 0

    context = {
        'username': request.user.username,
        'class': 'PBP A',
        'products': products,
        'last_login': request.COOKIES['last_login'],
        'total_stock': total_stock,
    }

    return render(request, "main.html", context)

def inventory(request):
    products = Product.objects.filter(user=request.user)
    context = {
        'username': request.user.username,
        'class': 'PBP A',
        'products': products,
        'last_login': request.COOKIES['last_login'],
    }
    return render(request, "inventory.html", context)

def create_product(request):
    form = ProductForm(request.POST or None)

    if form.is_valid() and request.method == "POST":
        product = form.save(commit=False)
        product.user = request.user
        product.save()
        return HttpResponseRedirect(reverse('main:inventory'))

    context = {'form': form}
    return render(request, "create_product.html", context)

def show_xml(request):
    data = Product.objects.all()
    return HttpResponse(serializers.serialize("xml", data), content_type="application/xml")

def show_json(request):
    data = Product.objects.all()
    return HttpResponse(serializers.serialize("json", data), content_type="application/json")

def show_xml_by_id(request, id):
    data = Product.objects.filter(pk=id)
    return HttpResponse(serializers.serialize("xml", data), content_type="application/xml")

def show_json_by_id(request, id):
    data = Product.objects.filter(pk=id)
    return HttpResponse(serializers.serialize("json", data), content_type="application/json")

def register(request):
    form = UserCreationForm()

    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your account has been successfully created!')
            return redirect('main:login')
    context = {'form':form}
    return render(request, 'register.html', context)

def login_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            response = HttpResponseRedirect(reverse("main:show_main")) 
            response.set_cookie('last_login', str(datetime.datetime.now()))
            return response
        else:
            messages.info(request, 'Sorry, incorrect username or password. Please try again.')
    context = {}
    return render(request, 'login.html', context)

def logout_user(request):
    logout(request)
    response = HttpResponseRedirect(reverse('main:login'))
    response.delete_cookie('last_login')
    return response

def add_amount(request, id):
    product = get_object_or_404(Product, pk=id)
    if product.amount >= 0:
        product.amount += 1
        product.save()
    return HttpResponseRedirect(reverse('main:inventory'))

def subtract_amount(request, id):
    product = get_object_or_404(Product, pk=id)
    if product.amount > 0:
        product.amount -= 1
        product.save()
    return HttpResponseRedirect(reverse('main:inventory'))

def edit_product(request, id):
    # Get product berdasarkan ID
    product = Product.objects.get(pk = id)

    # Set product sebagai instance dari form
    form = ProductForm(request.POST or None, instance=product)

    if form.is_valid() and request.method == "POST":
        # Simpan form dan kembali ke halaman awal
        form.save()
        return HttpResponseRedirect(reverse('main:inventory'))

    context = {'form': form}
    return render(request, "edit_product.html", context)

def delete_product(request, id):
    # Get data berdasarkan ID
    product = Product.objects.get(pk = id)
    # Hapus data
    product.delete()
    # Kembali ke halaman awal
    return HttpResponseRedirect(reverse('main:inventory'))

def home(request):
    return render(request, "home.html")

def get_product_json(request):
    products = Product.objects.filter(user=request.user)
    product_list = []
    for product in products:
        product_dict = {
            'pk': product.pk,
            'name': product.name,
            'description': product.description,
            'price': product.price,
            'amount': product.amount,
            'edit_url': reverse('main:edit_product', args=[product.pk]),
            'delete_url': reverse('main:delete_product', args=[product.pk]),
        }
        product_list.append(product_dict)
    return JsonResponse(product_list, safe=False)

@csrf_exempt
def add_product_ajax(request):
    if request.method == 'POST':
        name = request.POST.get("name")
        price = request.POST.get("price")
        description = request.POST.get("description")
        amount = request.POST.get("amount")
        user = request.user

        new_product = Product(name=name, price=price, description=description, amount=amount, user=user)
        new_product.save()

        return HttpResponse(b"CREATED", status=201)

    return HttpResponseNotFound()

@csrf_exempt
def create_product_flutter(request):
    if request.method == 'POST':
        
        data = json.loads(request.body)

        new_product = Product.objects.create(
            user = request.user,
            name = data["name"],
            amount = int(data["amount"]),
            description = data["description"]
        )

        new_product.save()

        return JsonResponse({"status": "success"}, status=200)
    else:
        return JsonResponse({"status": "error"}, status=401)