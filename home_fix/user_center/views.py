from django.shortcuts import render, redirect

from service.models import Order, Services
from user_center.models import Transaction
from user_center.query import provide_list_query
from users.forms import CustomUserChangeForm
from users.models import CustomUser
from django.db import connection
from django.db.models import Q

# Create your views here.
from utils import dictfetchall


def profile_view(request):
    if request.user.is_authenticated:
        user_id = request.user.id
        user = CustomUser.objects.get(id=user_id)
        user.password = None
        return render(request, "user_center/profile.html", context={"user": user})
    else:
        return redirect("basic:index")


def profile_editor_view(request):
    if request.user.is_authenticated:
        user_id = request.user.id
        user = CustomUser.objects.get(id=user_id)
        user.password = None
        if request.method == "POST":
            form = CustomUserChangeForm(request.POST, instance=request.user)
            if form.is_valid():
                form.save()
            return redirect("user_center:profile")
        else:
            return render(
                request, "user_center/profile_editor.html", context={"user": user}
            )
    else:
        return redirect("basic:index")


def request_view(request):
    if request.user.is_authenticated:
        user_id = request.user.id
        user = CustomUser.objects.get(id=user_id)
        # fetch data from Order table
        order_list = Order.objects.filter(user=user).order_by("-timestamp")
        if not hasattr(request, "info"):
            request.info = None
        return render(
            request,
            "user_center/my_request_page.html",
            context={"order_list": order_list, "info": request.info},
        )
    else:
        return redirect("basic:index")


def request_finish_view(request, order_id):
    if request.user.is_authenticated:
        request_user_id = request.user.id
        order = Order.objects.get(id=order_id)
        # this order doesn't belong to this user
        if order.user.id != request_user_id:
            return redirect("basic:index")
        else:
            coin_charged = order.service.coins_charged
            request_user = order.user
            provide_user = order.service.user
            # print(provide_user.coin)
            # print(coin_charged)
            # if provide_user.coin < coin_charged:
            #     print("xxxx")
            #     request.info = "your account doesn't have enough coins, please charge"
            #     return redirect("user_center:request")
            order.status = "finished"
            order.save()
            Transaction.objects.create(
                sender=request_user.email,
                receiver=provide_user.email,
                amount=coin_charged,
                service_type=order.service.service_category,
            )
            provide_user.coin -= coin_charged
            request_user.coin += coin_charged
            provide_user.save()
            request_user.save()
            return redirect("user_center:request")
    else:
        return redirect("basic:index")


def transaction_view(request):
    if request.user.is_authenticated:
        user_id = request.user.id
        user = CustomUser.objects.get(id=user_id)
        transactions = Transaction.objects.filter(
            Q(sender=user.email) | Q(receiver=user.email)
        )
        return render(
            request,
            "user_center/transaction.html",
            context={"transactions": transactions},
        )
        # get a list of transaction

    else:
        return redirect("basic:index")


def provide_view(request):
    if request.user.is_authenticated:
        user_id = request.user.id
        with connection.cursor() as cursor:
            cursor.execute(provide_list_query(user_id))
            result = dictfetchall(cursor)

        # object structure
        #  'service_id': 5, 'order_id': None, 'request_user_id': None,
        #  'order_time': None, 'server_provider': 1,
        #  'service_time': datetime.datetime(2022, 4, 4, 16, 26, 35, 36278),
        #  'status': None}
        #  request_user_id

        for row in result:
            # translate status
            # print(row)
            # there is no correspond order
            if row["status"] is None or row["status"] == "cancel":
                row["status"] = "no response"
                row["request_user_id"] = None
                row["order_time"] = None
            # "pending" mean a user choose this service
            if row["status"] == "pending":
                row["status"] = "picked"
            if row["request_user_id"] is not None:
                row["request_user_id"] = CustomUser.objects.get(
                    id=row["request_user_id"]
                ).first_name
        return render(
            request,
            "user_center/my_provide_page.html",
            context={"provide_list": result},
        )

    else:
        return redirect("basic:index")


def provide_accept_view(request, order_id):
    if request.user.is_authenticated:
        service_user_id = request.user.id
        order = Order.objects.get(id=order_id)
        service = order.service
        # this order doesn't belong to this user

        if service.user.id != service_user_id:
            return redirect("basic:index")
        if order.status != "pending":
            return redirect("basic:index")
        order.status = "in progress"
        order.save()
        return redirect("user_center:provide")
        # get a list of transaction

    else:
        return redirect("basic:index")


def provide_delete_view(request, service_id):
    if request.user.is_authenticated:
        service_user_id = request.user.id
        service = Services.objects.get(id=service_id)
        if service.user.id != service_user_id:
            return redirect("basic:index")
        service.delete()
        return redirect("user_center:provide")
    else:
        return redirect("basic:index")


def provide_cancel_view(request, order_id):
    if request.user.is_authenticated:
        service_user_id = request.user.id
        order = Order.objects.get(id=order_id)
        service = order.service
        if service.user.id != service_user_id:
            return redirect("basic:index")
        order.status = "cancel"
        service.visible = True
        order.save()
        service.save()
        return redirect("user_center:provide")

    else:
        return redirect("basic:index")


#
# def contact_view(request):
#     if request.user.is_authenticated:
#         user_id = request.user.id
#         user = CustomUser.objects.get(id=user_id)
#         print(user)
#     else:
#         return redirect("basic:index")
