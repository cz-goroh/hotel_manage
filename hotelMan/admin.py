import datetime, calendar, threading, time, sys, traceback, json
from decimal import *
from django.contrib import admin
from django.contrib.auth import models
from django.contrib.auth.models import User, Group, Permission
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_list_or_404, get_object_or_404
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Avg, Max, Min, Sum, Count
from django.db.models import Q, F, OuterRef, Subquery, ExpressionWrapper, DecimalField
# from access.admin import *
from django.contrib.admin import AdminSite
from .models import *
from .views import *
# Register your models here.

class PaydFilter(admin.SimpleListFilter):
    title = 'Оплата'
    parameter_name = 'lev_payd'

    def lookups(self, request, model_admin):
        """Возвращает список кортежей. Первый элемент в каждом
                 кортеж является закодированным значением для опции, которая будет
                 появляются в запросе URL. Вторым элементом является
                 удобочитаемое имя для опции, которая появится
                 в правой боковой панели"""
        return (
            # ('full', 'Полностью'),
            ('part', 'Есть'),
            ('no', 'Нет'),
        )


    def queryset(self, request, queryset):
        """ Возвращает отфильтрованный набор запросов на основе значения
         предоставляется в строке запроса и извлекается через
         `Self.value ()`."""
        value = self.value()


        return queryset
        # return queryset.filter(price__lt=F('payd'))

class BidAdmin(admin.ModelAdmin):
    list_display = ('id', 'empl', 'ins', 'begin', 'end', 'client', 'price', 'status',)
    change_list_template = 'hotelMan/bid/change_list.html'
    search_fields = ('id','client__name',)
    # readonly_fields = []
    list_filter = ('status', 'begin', 'end', 'ins','origin','price', PaydFilter, 'empl', 'room__facility', 'room__facility__district', 'room__facility__metro', 'room__category')
    date_hierarchy = 'ins'
    sortable_by = ('id', 'empl', 'ins', 'begin', 'end', 'client', 'price', 'status',)

    add_form_template = 'hotelMan/bid/add.html'

    def save_model(self, request, obj, form, change):
        tarif = obj.tarif
        td = obj.end- obj.begin
        if 'zalog' in request.GET and request.GET['zalog']:
            pt = Paytype.objects.all()[0]
            pay = Pay(bid=obj, sum=request.GET['zalog'], paytype=pt)
            pay.save()
        if tarif.unit == 'hour':
            period=td.hours
            if obj.end.minute < obj.begin.hour:
                period = period + 1
        elif tarif.unit == 'day':
            period = td.days
            if obj.end.hour < obj.begin.hour:
                period = period + 1

        # elif tarif.price_for =='month'
        #     period = td.monthes
        discounts = tarif.discounts.all().filter( min_period__gte=period).filter(max_period__lte=period)
        if discounts:
            disprices = [d.price for d in discounts]
            disprice = min(disprices)
            bid_price = period * disprice - obj.discount
        else:
            bid_price = tarif.price_0 * period - obj.discount
            # реализовать расчёт цен по дням?
        obj.price = Decimal(bid_price)
        # print(discounts)

        obj.save()

    def add_view(self, request, form_url='', extra_context=None):
        empl = Employee.objects.get(user=request.user)
        if 'fac' in request.GET:
            fac = Facility.objects.get(pk=request.GET['fac'])
        else:
            fac = None

        extra_context = {
            'empl': empl,
            'facility': fac,
            'tarifs': Tarif.objects.filter(partner=empl.partner)
        }

        return super(BidAdmin, self).add_view(request, form_url='', extra_context=extra_context)

    def dict_for_filters(self, request):

        empl = Employee.objects.get(user=request.user)
        empls = Employee.objects.filter(partner=empl.partner)
        bids = Bid.objects.filter(empl__in=empls)

        statuses = Bid.BID_STATUS

        origins = Origin.objects.all()
        pays = Pay.objects.all()
        orig = Origin.objects.all()
        metro = Metro.objects.all()
        room_cat = RoomCategory.objects.all()
        facitilytis = Facility.objects.filter(partner = empl.partner)
        district = District.objects.all()
        return {
            'empl': empl,
            'empls': empls,
            'bids': bids,
            'statuses': statuses,
            'origins': origins,
            'pays': pays,
            'orig': orig,
            'metro': metro,
            'room_cat': room_cat,
            'facitilytis': facitilytis,
            'district': district,
        }

    def by_payd(self, bid):
        pays_sum = Pay.objects.filter(bid=bid).aggregate(Sum('sum'))['sum__sum']
        if (pays_sum or 0) == bid.price:
            return 'f'
        elif (pays_sum or 0) == 0:
            return 'n'
        elif (pays_sum or 0) < bid.price or 0:
            return 'p'
        else:
            return None

    def changelist_view(self, request, extra_context=None):
        ek = self.dict_for_filters(request)

        extra_context = {
            'facitilytis': ek['facitilytis'],
            'empls': ek['empls'],
            'metro_st': ek['metro'],
            'room_cat': ek['room_cat'],
            'ok':'ok',
            # 'filters': filters_request,
            'bid_statuses': ek['statuses'],
            'origins': ek['origins'],
            'qs': Pay.objects.values_list('sum', flat=True)
            }
        return super(BidAdmin, self).changelist_view(request,  extra_context=extra_context)

    def payssum(self, bid_id):
        return Pay.objects.filter(bid__id=bid_id).aggregate(Sum('sum'))['sum__sum']

    def get_queryset(self, request):
        empl = Employee.objects.get(user=request.user)
        empls = Employee.objects.filter(partner=empl.partner)
        queryset = Bid.objects.all()
        pays = Pay.objects.all()
        if request.user.is_superuser:
            queryset = Bid.objects.all()
            # try:
        queryset = Bid.objects.all().annotate(paysum= Subquery(pays.filter(bid=OuterRef('pk')).values_list('sum', flat=True) ))


        # queryset = Bid.objects.all().annotate(pays=Sum(pays.values('sum')) )

        if 'lev_payd' in request.GET:
            value = request.GET['lev_payd']

            if value == 'full':
                queryset = queryset.filter(price__lte=F('paysum'))
            if value == 'no':
                queryset = queryset.filter(paysum=None)
            elif value == 'part':
                queryset = queryset.filter(price__gt=F('paysum'))
        return queryset

class PaytypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'code')
    list_editable = ('name', 'code')


class PartnerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_editable = ('name',)


class MetroAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'city')
    list_editable = ('name', 'city')


class CityAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'contry')
    list_editable = ('name', 'contry')


class ContryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_editable = ('name',)


class FacTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_editable = ('name',)


class DistrictAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'city')
    list_editable = ('name', 'city')

class RoomAdmin(admin.ModelAdmin):
    change_list_template = 'hotelMan/room/change_list.html'
    list_filter = ('facility__name', 'category__name', 'floor', 'tarif', 'status', 'category__osn_places', 'category__dop_places', )
    search_fields = ('id','name', )


class ClientAdmin(admin.ModelAdmin):
    change_list_template = 'hotelMan/client/change_list.html'


class OriginAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'url')
    list_editable = ('name', 'url')


class RoomCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'osn_places', 'dop_places')
    list_editable = ('name', 'osn_places', 'dop_places')


class FacilityAdmin(admin.ModelAdmin):
    list_display = ('name', 'partner', 'adres', 'for_channels', 'factype', 'district')


class PayAdmin(admin.ModelAdmin):
    list_display = ('id', 'bid', 'sum', 'paytype')


class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('id', 'ФИО', 'tel', 'Тип_сотрудника', 'money')
    search_fields = ('id','name','surname')
    list_filter = ('name','surname', 'rol')


class MyAdminSite(AdminSite):
    """текущие события- журнал, история операций """
    site_header='Отельер'
    site_title = 'Отельер'
    index_template = 'hotelMan/hotadmin_base.html'
    index_title = 'Календарь бронирования'

    def bid_inf(bid):

        if bid:
            pays_sum = Pay.objects.filter(bid__id=bid[0].id).aggregate(Sum('sum'))['sum__sum'] or 0
            return {
            'pays': pays_sum,
            'debt': bid[0].price - pays_sum,
            'days': (bid[0].end - bid[0].begin)
            }
        else:
            return None

    def room_dict(self, room, gettime, cal, iter_period):
        if not room.is_berth:
            daydict = { day:
                {'bid_info':Bid.objects.filter(room=room).filter(begin__lte=day + datetime.timedelta(days=1)).filter(end__gte =day).exclude(status='del'),
                'bid_flag':True,
                'bid_calc': MyAdminSite.bid_inf(Bid.objects.filter(
                                room=room).filter(begin__lte=day + datetime.timedelta(days=1)).filter(
                                end__gte =day).exclude(status='del'))
                }
            for day in iter_period
            }
            # day_d = {}
            bids_id_list = []
            for d,day_ff in daydict.items():

                if day_ff['bid_info'] and day_ff['bid_info'][0].id in bids_id_list:
                    daydict[d]['bid_flag'] = False
                if day_ff['bid_info']:
                    bids_id_list.append(day_ff['bid_info'][0].id)
            # print(bids_id_list)
            room_beds_dict = {}
        else:

            daydict = {}
            room_beds_dict = {
            bed.num:
                {str(day.day) + '_' + str(day.month):{
                    'bid_info':
                        Bid.objects.filter(bed__num=bed.num).filter(begin__lte=day+ datetime.timedelta(days=1)).filter(end__gte =day).exclude(status='del'),
                    'bid_flag':True,
                    'bid_calc': MyAdminSite.bid_inf(Bid.objects.filter(bed__num=bed.num).filter(begin__lte=day+ datetime.timedelta(days=1)).filter(end__gte =day).exclude(status='del'))
                     }
                for day in iter_period}
            for bed in Bed.objects.filter(room=room)}

            bids_id_list = []
            # print(room_beds_dict)
            for bed_num,days in room_beds_dict.items():
                # print(bed_num)
                for d,day_ff in days.items():
                    # print(day_ff[d])
                    if day_ff['bid_info'] and day_ff['bid_info'][0].id in bids_id_list:
                        room_beds_dict[ bed_num][d]['bid_flag'] = False

                    if day_ff['bid_info']:
                        bids_id_list.append(day_ff['bid_info'][0].id)
                    # pass
        return {
            'room': {
                'room_obj':room,
                'room_dict':daydict,
                'room_beds_dict': room_beds_dict
                },
            'beds': Bed.objects.filter(room=room),
            'daydict':daydict,
            }
    def rooms_for(self, request, fac, gettime):
        if 'show_free' in request.GET:
            period_bids = Bid.objects.filter(begin__lte=gettime).filter(end__gte=gettime)
            full_rooms = [fbid.room.id for fbid in period_bids]
            return Room.objects.filter(facility=fac).exclude(id__in=full_rooms)
        else:
            return Room.objects.filter(facility=fac)

    def dashboard(self,request):
        if 'prolong' in request.GET:
            prolong(request)
        if 'getdate' in request.GET:
            spl = request.GET['getdate'].split('-')
            gettime = datetime.date(int(spl[0]), int(spl[1]), int(spl[2]))
        else:
            gettime = datetime.datetime.now() # затем заменим на входное время


        cal = calendar.Calendar(0)
        empl = Employee.objects.get(user = request.user)

        if empl:
            facilitys = Facility.objects.filter(partner=empl.partner)
            if 'period' in request.GET:
                period = request.GET['period']
                iter_period = [gettime,]
                for_iter = gettime + datetime.timedelta(days=1)
                for day_plus in range(int(period)):
                    iter_period.append(for_iter)
                    for_iter = for_iter + datetime.timedelta(days=1)
            else:
                iter_period = [
                    i for i in cal.itermonthdates(gettime.year, gettime.month)
                        if i.month == gettime.month
                        ]
            # print(iter_period)

            if 'facility' in request.GET:
                facilitys = facilitys.filter(pk=request.GET['facility'])
            if 'metro' in request.GET:
                facilitys = facilitys.filter(metro=request.GET['metro'])
            if 'district' in request.GET:
                facilitys = facilitys.filter(district=request.GET['district'])

            facs = { fac:{ room : self.room_dict(room, gettime, cal, iter_period)
                for room in self.rooms_for(request, fac, gettime)}
            for fac in facilitys }

            cal_head = [d for d in iter_period ]
            # first_day = min(cal_head)
            # last_day = max(cal_head)
            # current_bids_query =  Bid.objects.filter(room__facility__in=facilitys).filter(
            #     (Q(begin__lte=first_day) & Q(end__gte=first_day) & Q(end__lte=last_day)) |
            #     (Q(begin__gte=first_day) & Q(end__gte=first_day) & Q(end__lte=last_day)) |
            #     (Q(begin__gte=first_day) & Q(begin__lte=last_day) & Q(end__gte=last_day)) |
            #     (Q(begin__lte=first_day) & Q(end__gte=last_day)))
            # if current_bids_query:
            #     cur_bids = {
            #     str(bid.room.facility.id) + '_' + str(bid.room.id) + '_' + str(bid.bed.id): bid
            #     for bid in current_bids_query }
            # else:
            #     cur_bids = None
            today = datetime.datetime.now()
            next_week = gettime + datetime.timedelta(days=7)
            prev_week = gettime - datetime.timedelta(days=7)
            next_month = gettime + datetime.timedelta(days=30)
            prev_month = gettime - datetime.timedelta(days=30)
            return {
                'facilitys': facs,
                # 'calendar': calend,
                'cal_head': cal_head,
                'today': str(today.year) + '-' + str(today.month) + '-' + str(today.day),

                'next_week': str(next_week.year) + '-' + str(next_week.month) + '-' + str(next_week.day),
                'prev_week': str(prev_week.year) + '-' + str(prev_week.month) + '-' + str(prev_week.day),
                'next_month': str(next_month.year) + '-' + str(next_month.month) + '-' + str(next_month.day),
                'prev_month': str(prev_month.year) + '-' + str(prev_month.month) + '-' + str(prev_month.day),
                'fd_month': str(today.year) + '-' + str(today.month) + '-' + str(1),
                'gettime': gettime,
            }
        else:
            return {}
    def each_context(self, request):
        if request.user.is_authenticated:
            ek = BidAdmin.dict_for_filters(self, request)
            dashb = self.dashboard(request)
            return {
            'site_title': self.site_title,
            'site_header': self.site_header,
            'site_url' : self.site_url,
            'has_permission' : self.has_permission(request),
            'available_apps' : self.get_app_list(request),
            'dashb': dashb,
            'facitilytis': ek['facitilytis'],
            'empls': ek['empls'],
            'metro_st': ek['metro'],
            'room_cat': ek['room_cat'],
            'district': ek['district'],
            'ok':'ok',
            # 'filters': filters_request,
            'bid_statuses': ek['statuses'],
            'origins': ek['origins'],
            'qs': Pay.objects.values_list('sum', flat=True)
            }
        else:
            return {
                'site_title': self.site_title,
                'site_header': self.site_header,
                'site_url' : self.site_url,
                'has_permission' : self.has_permission(request),
                'available_apps' : self.get_app_list(request),
            }


hotadmin = MyAdminSite(name='hotadmin')


hotadmin.register(Partner, PartnerAdmin)
hotadmin.register(District, DistrictAdmin)
hotadmin.register(FacType, FacTypeAdmin)
hotadmin.register(Facility, FacilityAdmin)
hotadmin.register(RoomCategory, RoomCategoryAdmin)
hotadmin.register(Room, RoomAdmin)
hotadmin.register(Discounts)
hotadmin.register(Paytype, PaytypeAdmin)
hotadmin.register(Tarif)
hotadmin.register(Client, ClientAdmin)
hotadmin.register(Employee, EmployeeAdmin)
hotadmin.register(Origin, OriginAdmin)
hotadmin.register(Bid, BidAdmin)
hotadmin.register(Pay, PayAdmin)
hotadmin.register(Bed)
hotadmin.register(Metro, MetroAdmin)
hotadmin.register(City, CityAdmin)
hotadmin.register(Contry, PartnerAdmin)
