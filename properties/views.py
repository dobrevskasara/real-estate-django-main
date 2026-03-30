from decimal import Decimal

import requests
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from properties.forms import PropertyForm
from properties.models import *

def property_list(request):

    properties = Property.objects.filter(status="approved").prefetch_related("images", "features")

    city = request.GET.get("city", "").strip()
    listing_type = request.GET.get("listing_type")
    property_type = request.GET.get("property_type")
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")
    min_area = request.GET.get("min_area")
    min_bedrooms = request.GET.get("bedrooms")
    feature_ids = request.GET.getlist("features")
    keyword = request.GET.get("q", "").strip()

    if city:
        properties = properties.filter(city__icontains=city)
    if listing_type:
        properties = properties.filter(listing_type=listing_type)
    if property_type:
        properties = properties.filter(property_type=property_type)
    if min_price:
        properties = properties.filter(price__gte=Decimal(min_price))
    if max_price:
        properties = properties.filter(price__lte=Decimal(max_price))
    if min_area:
        properties = properties.filter(area__gte=Decimal(min_area))
    if min_bedrooms:
        properties = properties.filter(bedrooms__gte=min_bedrooms)
    if feature_ids:
        properties = properties.filter(features__id__in=feature_ids)
    if keyword:
        properties = properties.filter(
            Q(custom_features__icontains=keyword) |
            Q(features__name__icontains=keyword)
        )

    properties = properties.distinct()

    sort_by = request.GET.get('sort', '-created_at')
    allowed_sorts = ['price', '-price', '-created_at', '-views']

    if sort_by in allowed_sorts:

        if sort_by == '-views' and not hasattr(Property, 'views'):
            properties = properties.order_by('-created_at')
        else:
            properties = properties.order_by(sort_by)
    else:
        properties = properties.order_by('-created_at')


    return render(request, "properties/properties.html", {
        "properties": properties,
        "features": Feature.objects.all(),
        "property_types": Property.PROPERTY_TYPE_CHOICES,
        "selected_listing_type": listing_type,
        "selected_features": feature_ids,
        "selected_property_type": property_type,
        "selected_city": city,
        "selected_keyword": keyword,
        "current_sort": sort_by,
    })

def property_details(request, id):
    property_obj = get_object_or_404(Property, id=id, status="approved")
    return render(request, "properties/property_details.html", {"property": property_obj})


@login_required
def create_property(request):
    if request.method == "POST":
        form = PropertyForm(request.POST, request.FILES)
        if form.is_valid():
            property_obj = form.save(commit=False)
            property_obj.owner = request.user
            property_obj.save()
            form.save_m2m()

            images = request.FILES.getlist("images")
            new_cover_index = request.POST.get("new_cover_image")

            for i, img in enumerate(images):
                PropertyImage.objects.create(
                    property=property_obj,
                    image=img,
                    is_cover=(str(i) == str(new_cover_index))
                )

            if property_obj.images.exists() and not property_obj.images.filter(is_cover=True).exists():
                first = property_obj.images.first()
                first.is_cover = True
                first.save()

            return redirect("profile")
    else:
        form = PropertyForm()

    return render(request, "properties/form.html", {
        "form": form
    })


@login_required
def edit_property(request, pk):
    property_obj = get_object_or_404(Property, pk=pk, owner=request.user)

    if request.method == "POST":
        form = PropertyForm(request.POST, request.FILES, instance=property_obj)
        if form.is_valid():
            edited = form.save(commit=False)
            edited.save()
            form.save_m2m()

            images_to_delete = request.POST.getlist("delete_images")
            if images_to_delete:
                PropertyImage.objects.filter(id__in=images_to_delete, property=edited).delete()

            new_images = request.FILES.getlist("images")
            new_cover_index = request.POST.get("new_cover_image")

            created_images = []
            for i, img in enumerate(new_images):
                new_obj = PropertyImage.objects.create(
                    property=edited,
                    image=img,
                    is_cover=(str(i) == str(new_cover_index))
                )
                created_images.append(new_obj)

            selected_cover = request.POST.get("cover_image")

            if selected_cover:
                edited.images.all().update(is_cover=False)
                edited.images.filter(id=selected_cover).update(is_cover=True)
            elif new_cover_index is not None and created_images:
                edited.images.all().update(is_cover=False)
                for i, img_obj in enumerate(created_images):
                    img_obj.is_cover = (str(i) == str(new_cover_index))
                    img_obj.save()

            if edited.images.exists() and not edited.images.filter(is_cover=True).exists():
                first = edited.images.first()
                first.is_cover = True
                first.save()

            return redirect("profile")

    else:
        form = PropertyForm(instance=property_obj)

    return render(request, "properties/form.html", {
        "form": form,
        "property": property_obj
    })


@login_required
def delete_property(request, pk):
    if request.method != "POST":
        return redirect("profile")

    property_obj = get_object_or_404(Property, pk=pk, owner=request.user)
    property_obj.delete()

    return redirect("profile")


def clean_value(value, default="Not provided"):
    return value.strip() if value and value.strip() else default


@require_POST
def generate_description(request):
    name = clean_value(request.POST.get("name"))
    property_type = clean_value(request.POST.get("property_type"))
    city = clean_value(request.POST.get("city"))
    location = clean_value(request.POST.get("location"))
    price = clean_value(request.POST.get("price"))
    area = clean_value(request.POST.get("area"))
    rooms = clean_value(request.POST.get("rooms"))
    bedrooms = clean_value(request.POST.get("bedrooms"))
    bathrooms = clean_value(request.POST.get("bathrooms"))
    custom_features = clean_value(request.POST.get("custom_features"), "None")
    ai_prompt = clean_value(request.POST.get("ai_prompt"), "None")

    selected_feature_ids = request.POST.getlist("features")

    selected_features = Feature.objects.filter(id__in=selected_feature_ids)

    features_text = ", ".join(
        selected_features.values_list("name", flat=True)
    ) if selected_features.exists() else "None"

    prompt = f"""
    Write one short real estate description in English.

    Use only these facts:
    Name: {name}
    Type: {property_type}
    City: {city}
    Location: {location}
    Price: {price} EUR
    Area: {area} m²
    Rooms: {rooms}
    Bedrooms: {bedrooms}
    Bathrooms: {bathrooms}
    Features: {features_text}
    Additional features: {custom_features}

    User wishes:
    {ai_prompt if ai_prompt else "None"}

    Rules:
    - One paragraph only
    - Maximum 3 sentences
    - Simple and factual
    - No headings
    - No bullet points
    - Do not repeat the input
    - Do not add missing details
    - Do not rename or upgrade features

    Return only the final paragraph.
    """

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3:8b",
                # "model": "tinyllama:latest",
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )
        response.raise_for_status()
        data = response.json()

        description = data.get("response", "").strip()

        if not description:
            return JsonResponse({
                "error": "No response returned from Ollama",
                "raw": data
            }, status=500)

        parts = description.split("\n\n")

        if len(parts) > 1:
            description = parts[1].strip()

        return JsonResponse({
            "description": description
        })

    except requests.RequestException as e:
        return JsonResponse({
            "error": f"Request failed: {str(e)}"
        }, status=500)
