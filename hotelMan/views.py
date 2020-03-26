from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import get_list_or_404, get_object_or_404
from django.db.models import Avg, Max, Min, Sum
from django.db.models import Q
from .models import *
# Create your views here.
def add_new_bid(request):
    return HttpResponse('add')

def prolong(request):
    bid = Bid.objects.get(pk=request.GET['bid'])
    if 'to_month' in request.GET:
        if (bid.end.month + 1) > 12:
            new_month = 1
            new_year = bid.end.year + 1
        else:
            new_month = bid.end.month + 1
            new_year = bid.end.year
        new_end = datetime.datetime( new_year, new_month,
                                    bid.end.day, bid.end.hour, bid.end.minute)
    elif 'prolong_date' in request.GET:
        spl = request.GET['prolong_date'].split('-')
        new_end = datetime.date(int(spl[0]), int(spl[1]), int(spl[2]))
    else:
        new_end = bid.end + datetime.timedelta(days=int(request.GET['prolong']))
    bid.end = new_end
    bid.save()
    if 'HTTP_REFERER' in request.META:
        return HttpResponseRedirect(request.META['HTTP_REFERER'])
    else:
        return HttpResponseRedirect('/hotadmin/')
