from django.shortcuts import render, redirect

from core.models import ContactMessage
from django.contrib import messages

from django.shortcuts import render
from properties.models import Property


# def home(request):
#     return render(request, "core/home.html")

def about(request):
    return render(request, "core/about.html")

def contact(request):
    return render(request, "core/contact.html")

def contact(request):
    if request.method == "POST":
        ContactMessage.objects.create(
            first_name=request.POST.get("first_name", "").strip(),
            last_name=request.POST.get("last_name", "").strip(),
            email=request.POST.get("email", "").strip(),
            phone=request.POST.get("phone", "").strip(),
            subject=request.POST.get("subject", "").strip(),
            message=request.POST.get("message", "").strip(),
        )
        messages.success(request, "Your message has been sent! We'll get back to you shortly.")
        return redirect("contact")

    return render(request, "core/contact.html")


def home(request):
    all_approved = Property.objects.filter(status="approved").prefetch_related("images").order_by('-created_at')

    context = {
        'featured_prop': all_approved.first(),
        'side_properties': all_approved[1:4],
        'bottom_properties': all_approved[4:7],
    }
    return render(request, "core/home.html", context)