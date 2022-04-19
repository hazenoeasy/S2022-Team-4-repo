import logging
from django.shortcuts import render, redirect

from admin_system.models import Report
from user_center.models import Transaction
from users.models import CustomUser
from service.models import Notifications, Services, Order
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model

# Create your views here.

from django.urls import reverse


def request_service_view(request):
    if request.user.is_authenticated:
        user_id = request.user.id
        user = CustomUser.objects.get(id=user_id)
        services = Services.objects.filter(visible=True)
        user.password = None
        return render(
            request,
            "service/request_services.html",
            context={"user": user, "services": services},
        )
    else:
        return redirect("basic:index")


@csrf_exempt
def offer_service_view(request):
    if request.method == "POST":
        user_id = request.user.id
        user = CustomUser.objects.get(id=user_id)
        user.password = None
        logging.warning(request.POST["category"])
        a = request.POST["description"]
        find = a.find('<p data-f-id="pbf" style="text-align: center; font-size: 14px;')
        if find != -1:
            a = a[:find]
        # can add some params validation
        print(request.POST)
        Services.objects.create(
            service_category=request.POST["category"],
            user=request.user,
            service_description=a,
            coins_charged=request.POST["coins"],
            street=request.POST["address"],
            state=request.POST["state"],
            country=request.POST["country"],
            zip=request.POST["postalcode"],
            long=request.POST["long"],
            lat=request.POST["lat"],
        )
        return redirect("service:request_service")
    #        return render(request, "base/request_services.html", context={"user": user, "services": services})
    else:
        if request.user.is_authenticated:
            user_id = request.user.id
            user = CustomUser.objects.get(id=user_id)
            user.password = None
            return render(
                request, "service/offer_services.html", context={"user": user}
            )
        else:
            return redirect("basic:index")


def request_service_confirm_view(request, service_id):
    if request.user.is_authenticated:
        user_id = request.user.id
        user = CustomUser.objects.get(id=user_id)
        service = Services.objects.get(id=service_id)
        ##Commission logic here
        commission = int(float(service.coins_charged) * (0.05))
        user.coin -= service.coins_charged + commission
        user.save()
        transaction = Transaction.objects.create(
            sender=user.email,
            receiver=service.user.email,
            amount=service.coins_charged,
            commission_fee=commission,
            service_type=service.service_category,
            status="pending",
        )
        Order.objects.create(user=user, service=service, transaction=transaction)

        service.visible = False
        service.save()
        Notifications.objects.create(
            user=user, service=service, status="pending", read=False
        )
        return redirect("user_center:request")
    else:
        return redirect("basic:index")


def service_detail_view(request, service_id):
    if request.user.is_authenticated:
        user_id = request.user.id
        user = CustomUser.objects.get(id=user_id)
        services = list(Services.objects.filter(id=service_id).all())
        message = ""
        if user.coin < services[0].coins_charged:
            message = "not enough coins"
        logging.warning(services)
        user.password = None

        is_same = False
        if services[0].user_id == user.id:
            is_same = True

        commission = int(float(services[0].coins_charged) * 0.05)
        return render(
            request,
            "service/service_detail.html",
            context={
                "is_same": is_same,
                "user": user,
                "services": services[0],
                "message": message,
                "commission": commission,
            },
        )
    else:
        return redirect("basic:index")


def services_locations(request):
    if not request.user.is_authenticated:
        return redirect("users:login")
    # User = get_user_model()
    # users = User.objects.all()
    services = Services.objects.filter(visible=True)
    serv = []
    for i in services:
        temp = []
        temp.append(float(i.lat))
        temp.append(float(i.long))
        serv.append(temp)
    userloc = [float(request.user.lat), float(request.user.long)]

    return render(
        request,
        "service/services_locations.html",
        context={"services": serv, "user": userloc},
    )


def report_view(request, service_id):
    if request.user.is_authenticated:
        service = Services.objects.get(id=service_id)
        reporter = CustomUser.objects.get(id=request.user.id)
        content = request.POST.get("discription")
        Report.objects.create(service=service, reporter=reporter, content=content)
        return redirect(
            reverse("service:service_detail", kwargs={"service_id": service_id})
        )
    else:
        return redirect("basic:index")
