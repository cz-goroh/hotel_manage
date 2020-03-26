import datetime
from django.utils import timezone

from django.db import models
from django.contrib.auth.models import User, UserManager
from django.db.models import Avg, Max, Min, Sum


# Create your models here.

class Contry(models.Model):
    name = models.CharField("Название",max_length=255)
    def __str__(self):
        return self.name


class Partner(models.Model):
    name = models.CharField("Название",max_length=255)

    def __str__(self):
        return self.name
    class Meta:
        verbose_name = 'Фирма'
        verbose_name_plural = 'Фирмы'

class City(models.Model):
    name = models.CharField("Название",max_length=255)
    contry = models.ForeignKey(Contry, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
    class Meta:
        verbose_name = 'Город'
        verbose_name_plural = 'Города'


class  District(models.Model):
    """Районы добавить город и страна станция метро"""
    name = models.CharField("Название",max_length=255)
    city = models.ForeignKey(City, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.name
    class Meta:
        verbose_name = 'Район'
        verbose_name_plural = 'Районы'


class Metro(models.Model):
    name = models.CharField("Название",max_length=255)
    city = models.ForeignKey(City, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
    class Meta:
        verbose_name = 'Станция метро'
        verbose_name_plural = 'Станции метро'


class FacType(models.Model):
    """типы- хостелы, аппартаменты, коттеджи, коворкинги, почасовые"""
    name = models.CharField("Название",max_length=255)

    def __str__(self):
        return self.name
    class Meta:
        verbose_name = 'Тип обьекта'
        verbose_name_plural = 'Типы объектов'


class Facility(models.Model):
    """
        типы- хостелы, аппартаменты, коттеджи, коворкинги, почасовые
        партнерские отношения между владельцами, цена - два варианта нарастает или процент
    """
    name = models.CharField("Название",max_length=255)
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE)
    adres = models.CharField("Адрес", max_length=255)
    for_channels = models.BooleanField("Доступен для каналов продаж", default=True)
    factype = models.ForeignKey(FacType, on_delete=models.CASCADE, verbose_name="Тип объекта")
    district = models.ForeignKey(District, on_delete=models.CASCADE, verbose_name="Район")
    metro = models.ForeignKey(Metro, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return self.name
    class Meta:
        verbose_name = 'Обьект'
        verbose_name_plural = 'Обьекты'


class RoomCategory(models.Model):
    """цена за сутки/ неделю/ месяц/ произвольный период"""
    name = models.CharField("Название",max_length=255)
    osn_places = models.SmallIntegerField("Основных мест")
    dop_places = models.SmallIntegerField("Дополнительных мест")

    class Meta:
        verbose_name = 'Категория комнат'
        verbose_name_plural = 'Категории Комнат'
    def __str__(self):
        return self.name


class Room(models.Model):
    ROOM_STATUS = (('active', 'Активен'),('cleaning', 'Уборка'), ('noactive', ' Неактивный'), ('rem', 'Ремонт'))
    name = models.CharField("Название",max_length=255)
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, verbose_name="Объект")
    category = models.ForeignKey(RoomCategory, on_delete=models.CASCADE, verbose_name="Категория")
    floor = models.SmallIntegerField("Этаж")
    tarif = models.ForeignKey('Tarif', on_delete=models.CASCADE, verbose_name="Тариф")
    status = models.CharField("Статус", max_length=255,choices=ROOM_STATUS)
    is_berth = models.BooleanField("Бронировать спальное место", default=False)
    # tarif = ForeignKey("Tarif", on_delete=)
    def status_verbose(self):
        return dict(Room.ROOM_STATUS)[self.status]
    status_verb = property(status_verbose)

    class Meta:
        verbose_name = 'Комната'
        verbose_name_plural = 'Комнаты'
    def __str__(self):
        return self.name + ' ' + self.facility.name


class Bed(models.Model):
    BED_TYPE = (('once', 'Одноместная'), ('double', 'Двухместнвя'), ('yarus1', '1 ярус двухъярусной'), ('yarus2', '2 ярус двухъярусной'))
    num = models.CharField("Номер",max_length=255)
    type = models.CharField("Тип",max_length=255, choices=BED_TYPE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, verbose_name="Комната", blank=True, null=True)

    class Meta:
        verbose_name = 'Спальное место'
        verbose_name_plural = 'Спальные места'
    def __str__(self):
        return 'ID'+ str(self.id)  + ' Объект:'  + self.room.facility.name + ' Комната:' + self.room.name + ' Место:' + self.num


class Discounts(models.Model):
    """Если не находим тариф здесь, то берём из базовых значений"""
    UNITS = (('hour', 'Час'), ('day', 'День'), ('month', 'Месяц'))
    name = models.CharField("Название",max_length=255)
    max_period = models.SmallIntegerField("Максимльный период в часах/днях/месяцах")
    min_period = models.SmallIntegerField("Минимальный период в часах/днях/месяцах")
    price = models.DecimalField(max_digits=19, decimal_places=2, verbose_name="Цена за единицу периода")
    dop_place_price = models.DecimalField(max_digits=19, decimal_places=2, verbose_name="Цена для дополнительных мест", blank=True, null=True)

    class Meta:
        verbose_name = 'Система скидок'
        verbose_name_plural = 'Системы скидок'
    def __str__(self):
        return self.name


class Paytype(models.Model):
    name = models.CharField("Название",max_length=255)
    code = models.CharField("Код",max_length=255)

    class Meta:
        verbose_name = 'Способ оплаты'
        verbose_name_plural = 'Спосбы оплаты'
    def __str__(self):
        return self.name

class Tarif(models.Model):

    PRICE_FOR = (('room', 'весь номер'), ('bed', 'человека'))
    UNITS = (('hour', 'Час'), ('day', 'День'), ('month', 'Месяц'))

    name = models.CharField("Название",max_length=255)
    descript = models.TextField("Описание тарифа")
    price_for = models.CharField("Цена за:", max_length=255, choices=PRICE_FOR)
    min_period = models.SmallIntegerField("Минимальный срок бронирования, единиц:")
    unit = models.CharField("Временная единица", max_length=20, choices=UNITS)
    discounts = models.ManyToManyField(Discounts, verbose_name="Системы скидок", blank=True, null=True)
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE, blank=True, null=True)
    # варианты оплаты создавать доп свойство в отдельной таблице many_to_many
    paytype = models.ManyToManyField(Paytype, verbose_name="Способы оплаты")
    # ch_in_pay = models.BooleanField("Оплата при заселении", default=True)
    # online_pay = models.BooleanField("Оплата онлайн", default=True)
    # bank_pay = models.BooleanField("Оплата по банковским реквизитам", default=True)
    # cash_pay = models.BooleanField("Наличные", default=True)
    # card_pay = models.BooleanField("Банковская карта", default=True)

    # сделать фиксированной
    dop_place_price = models.DecimalField(max_digits=19, decimal_places=2, verbose_name="Цена для дополнительных мест", blank=True, null=True)


    # закрыть н заезд
    cls_chin_0 = models.BooleanField("Закрыть на заезд:пн", default=False)
    cls_chin_1 = models.BooleanField("Закрыть на заезд:вт", default=False)
    cls_chin_2 = models.BooleanField("Закрыть на заезд:ср", default=False)
    cls_chin_3 = models.BooleanField("Закрыть на заезд:чт", default=False)
    cls_chin_4 = models.BooleanField("Закрыть на заезд:пт", default=False)
    cls_chin_5 = models.BooleanField("Закрыть на заезд:сб", default=False)
    cls_chin_6 = models.BooleanField("Закрыть на заезд:вс", default=False)

    # закрыть на выезд
    cls_evict_0 = models.BooleanField("Закрыть на выезд:пн", default=False)
    cls_evict_1 = models.BooleanField("Закрыть на выезд:вт", default=False)
    cls_evict_2 = models.BooleanField("Закрыть на выезд:ср", default=False)
    cls_evict_3 = models.BooleanField("Закрыть на выезд:чт", default=False)
    cls_evict_4 = models.BooleanField("Закрыть на выезд:пт", default=False)
    cls_evict_5 = models.BooleanField("Закрыть на выезд:сб", default=False)
    cls_evict_6 = models.BooleanField("Закрыть на выезд:вс", default=False)

    # Цены по дням недели
    price_0 = models.DecimalField(max_digits=19, decimal_places=2, verbose_name="Цена в Понедельник")
    price_1 = models.DecimalField(max_digits=19, decimal_places=2, verbose_name="Цена во Вторник")
    price_2 = models.DecimalField(max_digits=19, decimal_places=2, verbose_name="Цена в Среду")
    price_3 = models.DecimalField(max_digits=19, decimal_places=2, verbose_name="Цена в Четверг")
    price_4 = models.DecimalField(max_digits=19, decimal_places=2, verbose_name="Цена в Пятницу")
    price_5 = models.DecimalField(max_digits=19, decimal_places=2, verbose_name="Цена в Субботу")
    price_6 = models.DecimalField(max_digits=19, decimal_places=2, verbose_name="Цена в Воскресенье")


    class Meta:
        verbose_name = 'Тариф'
        verbose_name_plural = 'Тарифы'
    def __str__(self):
        return self.name


class Client(models.Model):
    SEX = (('m', 'Мужской'), ('w', 'Женский'))
    surname = models.CharField("Фамилия", max_length=255, blank=True, null=True)
    name = models.CharField("Имя", max_length=255)
    otchestvo = models.CharField("Отчество", max_length=255, blank=True, null=True)
    dop_descr = models.CharField("Дополнительные данные", max_length=255)
    tel = models.CharField("Тел", max_length=255)
    email = models.CharField("Email", max_length=255)
    adres = models.CharField("Адрес", max_length=255, blank=True, null=True)
    is_vip = models.BooleanField("в списке VIP", default=False)
    is_black = models.BooleanField("В чёрном списке", default=False)
    is_alien = models.BooleanField("Иностранец", default=False)
    sex = models.CharField("Пол", max_length=2, choices=SEX)

    pas_type = models.CharField("Удостоверение личности", max_length=255)
    pas_ser_num = models.CharField("Удостоверение личности: Серия и номер", max_length=255)# Серия и номер
    pas_data = models.DateField("Удостоверение личности: Дата выдачи")
    pas_vidan = models.CharField("Выдан(название подразделения)", max_length=255)
    pas_birth = models.DateField("Дата рождения")# Дата рождения
    coment = models.TextField("Комментарий", blank=True, null=True )

    photo1 = models.ImageField("Документ1", blank=True, null=True)
    photo2 = models.ImageField("Документ2", blank=True, null=True)
    photo3 = models.ImageField("Документ3", blank=True, null=True)
    photo4 = models.ImageField("Документ4", blank=True, null=True)
    photo5 = models.ImageField("Документ5", blank=True, null=True)

    # фото документа клиента, много фоток до 5
    #                                  реферал, менеджер
    def __str__(self):
        return self.name


class Employee(models.Model):
    """вручную выставлять права дл разных типов сотрудников- создать новую базу типов сотрудников,
    ограничения по датам проведения операций
    система штрафов для сотрудников
    последние действия сотрудников
    """
    ROL = (('manager', 'Менеджер'), ('direct', 'Руководство'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    tel = models.CharField("Телефон", max_length=255)
    rol = models.CharField("Тип", max_length=255, choices=ROL)
    surname = models.CharField("Фамилия", max_length=255)
    name = models.CharField("Имя", max_length=255)
    otchestvo = models.CharField("Отчество", max_length=255)
    for_contract = models.TextField("Основание для договора")
    money = models.DecimalField(max_digits=19, decimal_places=2, verbose_name="Счёт", default=0)
    birth_day = models.DateField("Дата рождения", blank=True, null=True)
    pas_num = models.CharField("Серия, номер паспорта", max_length=255, blank=True, null=True)
    pas_date = models.DateField("Паспорт выдан", blank=True, null=True)
    pas_mvd = models.CharField("Кем выдан", max_length=255, blank=True, null=True)
    adres = models.CharField("Адрес", max_length=255, blank=True, null=True)

    partner = models.ForeignKey(Partner, on_delete=models.CASCADE)
    Facility
    photo = models.ImageField("Фото сотрудника", blank=True, null=True)

    def get_fio(self):
        return self.surname + ' ' + self.name + ' ' + self.otchestvo

    ФИО = property(get_fio)

    def rol_verbose(self):
        return dict(Employee.ROL)[self.rol]
    Тип_сотрудника = property(rol_verbose)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Управление сотрудниками'


class Origin(models.Model):
    name = models.CharField("Название",max_length=255)
    url = models.CharField("URL",max_length=255)

    def __str__(self):
        return self.name
    class Meta:
        verbose_name = 'Источник бронирования'
        verbose_name_plural = 'Источники бронирования'


class Service(models.Model):
    name = models.CharField("Название",max_length=255)
    price = models.DecimalField(max_digits=19, decimal_places=2, verbose_name="Сумма")
    partner = models.ForeignKey(Partner, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
    class Meta:
        verbose_name = 'Источник бронирования'
        verbose_name_plural = 'Источники бронирования'


class Pay(models.Model):
    bid = models.ForeignKey("Bid", on_delete=models.CASCADE, verbose_name="Заявка")
    sum = models.DecimalField(max_digits=19, decimal_places=2, verbose_name="Сумма")
    paytype = models.ForeignKey(Paytype, on_delete=models.CASCADE, verbose_name="Способ оплаты")

    class Meta:
        verbose_name = 'Платёж'
        verbose_name_plural = 'Платежи'



class Bid(models.Model):
    # резерв, бронь, проживание, оплачено, незаезд-оплачено, свободен
    BID_STATUS = (
    ('reserved', 'Резерв'),
     ('bron', 'Бронь'),
     ('live', 'Проживание'),
     ('no_checkin', 'Незаезд'),
      ('debt', 'Задолженность'),
       ('del', 'Удалено'),)
    begin = models.DateTimeField("Заезд")
    end = models.DateTimeField("Выезд")
    ins = models.DateTimeField("время поступления", auto_now_add=True)
    room = models.ForeignKey(Room, verbose_name="Комната", on_delete=models.CASCADE)
    bed = models.ForeignKey(Bed, verbose_name="Спальное место", on_delete=models.CASCADE, blank=True, null=True)
    empl = models.ForeignKey(Employee, verbose_name="Сотрудник", on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=19, decimal_places=2, verbose_name="Стоимость")
    tarif = models.ForeignKey(Tarif, verbose_name="Тариф", on_delete=models.CASCADE)
    status = models.CharField("Статус бронирования", max_length=10, choices=BID_STATUS)
    origin = models.ForeignKey(Origin, verbose_name="Источник", on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, null=True, blank=True,verbose_name="Клиент")
    #  услуги
    coment = models.CharField("Комментарий", max_length=255, blank=True, null=True)
    discount = models.DecimalField(max_digits=19, decimal_places=2, verbose_name="Скидка", default=0)
    # quantity = SmallIntegerField("Количе")

    def get_payd(self):
        pays = Pay.objects.filter(bid=self)
        pays_sum = pays.aggregate(Sum('sum'))['sum__sum']
        return pays_sum or 0
        # return 'ok'

    payd = property(get_payd)

    def get_debt(self):
        pass

    debt = property(get_debt)

    def get_bed(self):
        return self.bed or 0

    show_bed = property(get_bed)

    def status_verbose(self):
        return dict(Bid.BID_STATUS)[self.status]
    status_verb = property(status_verbose)

    def statuses(self):
        return dict(Bid.BID_STATUS)
    statuses = property(status_verbose)

    def __str__(self):
        return self.room.name + ' ' + self.room.facility.name

    class Meta:
        verbose_name = 'Бронирование'
        verbose_name_plural = 'Бронирования'


class Doserv(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    bid = models.ForeignKey(Bid, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=19, decimal_places=2, verbose_name="Стоимость")
