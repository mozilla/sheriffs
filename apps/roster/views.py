import datetime
from django import http
from django.shortcuts import redirect, get_object_or_404
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.sites.models import RequestSite
from django.template import Context, loader
from django.contrib.auth.models import User
from django.utils import simplejson as json
from django.db.models import Max
from django.conf import settings
from django.core.mail import send_mail
from django.contrib import messages
from django.db import transaction
from django.core.paginator import Paginator, EmptyPage, InvalidPage
import jingo
import forms
from utils.decorators import staff_required
from utils import get_user_name
from models import Slot, Swap


@transaction.commit_on_success
@staff_required
def initialize(request):
    data = {}
    users = User.objects.all().order_by('first_name', 'username')
    if request.method == 'POST':
        form = forms.InitializeRosterForm(data=request.POST)
        if form.is_valid():
            usernames = form.cleaned_data['usernames']
            starting = form.cleaned_data['starting']
            until = form.cleaned_data['until']
            replace_existing = True #form.cleaned_data['replace_existing']

            usernames = [x.strip() for x in usernames.splitlines() if x.strip()]
            user_objects = [User.objects.get(username=x)
                            for x in usernames]
            date = starting
            increment = 0
            while date <= until:
                if date.strftime('%A') in ('Saturday', 'Sunday'):
                    date += datetime.timedelta(days=1)
                    continue
                if replace_existing:
                    Slot.objects.filter(date=date).delete()
                Slot.objects.create(
                  user=user_objects[increment % len(usernames)],
                  date=date,
                )
                date += datetime.timedelta(days=1)
                increment += 1
            return redirect(reverse('roster.index'))
    else:
        if not Slot.objects.all().count():
            initial = {'until': (datetime.datetime.today() +
                                 datetime.timedelta(days=users.count())),
                       'starting': datetime.datetime.today()}
        else:
            last_day = Slot.objects.aggregate(Max('date'))['date__max']
            usernames = []
            for slot in Slot.objects.order_by('-date').select_related('user'):
                if slot.user.username in usernames:
                    break
                else:
                    usernames.append(slot.user.username)
            usernames.reverse()
            initial = {'starting': last_day + datetime.timedelta(days=1),
                       'until': last_day + datetime.timedelta(days=1 + len(usernames)),
                       'usernames': '\n'.join(usernames)}

        form = forms.InitializeRosterForm(initial=initial)
    data['users'] = users
    data['form'] = form
    return jingo.render(request, 'roster/initialize.html', data)

@transaction.commit_on_success
@staff_required
def replace(request):
    data = {}
    today = datetime.date.today()
    if request.method == 'POST':
        form = forms.ReplaceRosterForm(data=request.POST)
        if form.is_valid():
            starting = form.cleaned_data['starting']
            if not starting:
                starting = today
            until = form.cleaned_data['until']
            if not until:
                until = Slot.objects.aggregate(Max('date'))['date__max']
            from_username = form.cleaned_data['from_username']
            from_user = User.objects.get(username__iexact=from_username)
            to_username = form.cleaned_data['to_username']
            to_user = User.objects.get(username__iexact=to_username)
            count = 0
            for slot in Slot.objects.filter(date__gte=starting,
                                            date__lte=until,
                                            user=from_user):
                slot.user = to_user
                slot.save()
                count += 1

            messages.info(request, "%s replaced %d slots from %s" %
                          (get_user_name(to_user),
                           count,
                           get_user_name(from_user)))

            return redirect(reverse('roster.index'))
    else:
        initial = {'starting': today}
        form = forms.ReplaceRosterForm(initial=initial)
    data['form'] = form
    return jingo.render(request, 'roster/replace.html', data)

@transaction.commit_on_success
@staff_required
def insert(request):
    data = {}
    in_slots = set()
    for slot in Slot.objects.all():
        in_slots.add(slot.user_id)

    users = (User.objects.exclude(pk__in=in_slots)
             .order_by('first_name', 'username'))
    if request.method == 'POST':
        form = forms.InsertRosterForm(data=request.POST)
        if form.is_valid():
            date = form.cleaned_data['starting']
            username = form.cleaned_data['username']
            user = User.objects.get(username__iexact=username)
            users = set()
            insert_after_user = None
            for slot in Slot.objects.filter(date__gte=date).order_by('date'):
                slot.bump_date(1, skip_weekend=True)
                Slot.objects.create(
                  user=user,
                  date=slot.date
                )

            raise NotImplementedError
            user_name = get_user_name(user)
            messages.info(request, '%s insert on %s going forward' %
                          (user_name,
                           date.strftime(settings.DEFAULT_DATE_FORMAT)))
    else:
        initial = {'starting': get_next_starting_date()}
        form = forms.InsertRosterForm(initial=initial)
    data['form'] = form
    data['users'] = users
    return jingo.render(request, 'roster/insert.html', data)

def get_next_starting_date(today=None):
    """return a date that is the date after one cycle of users start today.

    So if today is Friday and you have this:

        Friday   : Tom     (today)
        (note how weekends are skipped)
        Monday   : Dick
        Tuesday  : Harry
        Wednesday: Tom
        Thursdag : Dick
        Friday  : Harry

    Then, the date to return is Wednesday because then it's back to Tom again.
    """
    if today is None:
        today = datetime.date.today()
    try:
        Slot.objects.get(date=today)
    except Slot.DoesNotExist:
        return today

    users = []
    for slot in Slot.objects.filter(date__gte=today):
        if slot.user in users:
            return slot.date
        users.append(slot.user)


def index(request):
    data = {}
    page = request.GET.get('page')
    today = datetime.date.today()

    if request.GET.get('include_past'):
        include_past = '1'
        filter = {}
    else:
        filter = {'date__gte': today}
        include_past = ''
    slots = (Slot.objects.filter(**filter)
             .order_by('date').select_related('user'))
    SLOTS_PER_PAGE = 10
    paginator = Paginator(slots, SLOTS_PER_PAGE)
    default_page = 1
    if 'page' not in request.GET and include_past:
        # go to today's page
        count_past = Slot.objects.filter(date__lt=today).count()
        default_page = 1 + count_past / SLOTS_PER_PAGE
        print default_page

    try:
        page = int(request.GET.get('page', default_page))
    except ValueError:
        raise http.Http404

    try:
        slots = paginator.page(page)
    except (EmptyPage, InvalidPage):
        slots = paginator.page(paginator.num_pages)

    data['include_past'] = include_past
    data['slots'] = slots
    return jingo.render(request, 'roster/index.html', data)


def info_json(request):
    pk = request.GET.get('pk')
    if not pk:
        raise http.Http404("No 'pk'")
    slot = get_object_or_404(Slot, pk=pk)
    user_name = get_user_name(slot.user)
    data = {
      'pk': slot.pk,
      'date': slot.date.strftime(settings.DEFAULT_DATE_FORMAT),
      'name': user_name,
      'swap_needed': slot.swap_needed,
    }
    return http.HttpResponse(json.dumps(data))

@transaction.commit_on_success
@require_POST
@login_required
def offer_swap(request):
    pk = request.POST.get('pk')
    if not pk:
        raise http.Http404("No 'pk'")
    slot = get_object_or_404(Slot, pk=pk)
    slot_user_name = get_user_name(slot.user)
    user_name = get_user_name(request.user)
    comment = request.POST.get('comment', u'').strip()
    swap = Swap.objects.create(
      slot=slot,
      user=request.user,
      type=Swap.TYPE_OFFER,
      comment=comment,
    )
    base_url = '%s://%s' % (request.is_secure() and 'https' or 'http',
                            RequestSite(request).domain)
    accept_url = base_url + reverse('roster.accept_swap', args=[swap.uuid])
    decline_url = base_url + reverse('roster.decline_swap', args=[swap.uuid])

    template = loader.get_template('roster/offer_swap.txt')
    context = {
      'your_name': slot_user_name,
      'user_name': user_name,
      'slot': slot,
      'settings': settings,
      'accept_url': accept_url,
      'decline_url': decline_url,
      'date_formatted': slot.date.strftime(settings.DEFAULT_DATE_FORMAT),
      'comment': comment,
    }
    body = template.render(Context(context)).strip()
    subject = 'Offer to swap Sheriff duty'
    from_ = settings.SEND_EMAIL_FROM
    tos = [slot.user.email]
    worked = send_mail(subject, body, from_, tos)

    if worked:
        messages.info(request,
                      'An email as been sent to %s' %
                        ', '.join(tos))
    else:
        messages.warning(request,
                        'Email could NOT be sent to %s' %
                          ', '.join(tos))
    return redirect(reverse('cal.home'))


@transaction.commit_on_success
@require_POST
@login_required
def request_swap(request):
    pk = request.POST.get('pk')
    if not pk:
        raise http.Http404("No 'pk'")
    slot = get_object_or_404(Slot, pk=pk)
    user_name = get_user_name(request.user)

    slot.swap_needed = True
    slot.save()

    comment = request.POST.get('comment', u'').strip()
    swap = Swap.objects.create(
      slot=slot,
      user=None,
      type=Swap.TYPE_REQUEST,
      comment=comment,
    )
    base_url = '%s://%s' % (request.is_secure() and 'https' or 'http',
                            RequestSite(request).domain)
    accept_url = base_url + reverse('roster.accept_swap', args=[swap.uuid])
    #decline_url = base_url + reverse('roster.decline_swap', args=[swap.uuid])

    template = loader.get_template('roster/request_swap.txt')
    context = {
      'your_name': user_name,
      'slot': slot,
      'settings': settings,
      'accept_url': accept_url,
      #'decline_url': decline_url,
      'date_formatted': slot.date.strftime(settings.DEFAULT_DATE_FORMAT),
      'comment': comment,
    }
    body = template.render(Context(context)).strip()
    subject = 'Request to swap Sheriff duty'
    from_ = request.user.email
    tos = [settings.MAILINGLIST_EMAIL]
    worked = send_mail(subject, body, from_, tos)

    if worked:
        messages.info(request,
                      'An email as been sent to %s' %
                        ', '.join(tos))
    else:
        messages.warning(request,
                        'Email could NOT be sent to %s' %
                          ', '.join(tos))
    return redirect(reverse('cal.home'))




@transaction.commit_on_success
def accept_swap(request, uuid):
    swap = get_object_or_404(Swap, uuid=uuid)
    if swap.type == Swap.TYPE_REQUEST:
        # then you have to be logged in
        if not request.user.is_authenticated():
            from django.contrib.auth import REDIRECT_FIELD_NAME
            url = settings.LOGIN_URL
            url += '?%s=%s' % (REDIRECT_FIELD_NAME, request.path)
            return redirect(url)

    if swap.slot.date < datetime.date.today():
        raise http.Http404("Too late")
    if swap.state != Swap.STATE_UNANSWERED:
        return http.HttpResponse("Too late. Swap already %s" %
            swap.get_state_display())

    swap.state = Swap.STATE_ACCEPTED
    if swap.type == Swap.TYPE_REQUEST:
        swap.user = request.user
        swap.slot.swap_needed = False
        swap.slot.save()
    swap.modify_date = datetime.datetime.now()

    swap.save()

    swap.slot.user = swap.user
    swap.slot.save()
    user_name = get_user_name(swap.slot.user)
    swap_user_name = get_user_name(swap.user)
    type_friendly = swap.type == Swap.TYPE_OFFER and 'offer' or 'request'
    from_ = settings.SEND_EMAIL_FROM
    tos = [swap.user.email]
    template = loader.get_template('roster/swap_accepted.txt')
    context = {
      'your_name': swap_user_name,
      'user_name': user_name,
      'swap': swap,
      'type_friendly': type_friendly,
      'settings': settings,
      'date_formatted': swap.slot.date.strftime(settings.DEFAULT_DATE_FORMAT),
    }
    body = template.render(Context(context)).strip()
    subject = ('Sheriff swap %s accepted' % type_friendly)
    worked = send_mail(subject,
                       body,
                       from_,
                       tos)

    messages.info(request, '%s slot accepted'
                  % swap.slot.date.strftime(settings.DEFAULT_DATE_FORMAT))
    return redirect(reverse('cal.home'))

@transaction.commit_on_success
def decline_swap(request, uuid):
    swap = get_object_or_404(Swap, uuid=uuid)
    if swap.slot.date < datetime.date.today():
        raise http.Http404("Too late")
    if swap.state != Swap.STATE_UNANSWERED:
        return http.HttpResponse("Too late. Swap already %s" %
            swap.get_state_display())
    swap.state = Swap.STATE_DECLINED
    swap.modify_date = datetime.datetime.now()
    swap.save()
    user_name = get_user_name(swap.slot.user)
    swap_user_name = get_user_name(swap.user)
    type_friendly = swap.type == Swap.TYPE_OFFER and 'offer' or 'request'
    from_ = settings.SEND_EMAIL_FROM
    tos = [swap.user.email]
    template = loader.get_template('roster/swap_declined.txt')
    context = {
      'your_name': swap_user_name,
      'user_name': user_name,
      'swap': swap,
      'type_friendly': type_friendly,
      'settings': settings,
      'date_formatted': swap.slot.date.strftime(settings.DEFAULT_DATE_FORMAT),
    }
    body = template.render(Context(context)).strip()
    subject = ('Sheriff swap %s decline' % type_friendly)
    worked = send_mail(subject,
                       body,
                       from_,
                       tos)

    messages.info(request, '%s slot declined'
                  % swap.slot.date.strftime(settings.DEFAULT_DATE_FORMAT))
    return redirect(reverse('cal.home'))


@transaction.commit_on_success
@staff_required
def replace_slot(request, pk):
    data = {}
    slot = get_object_or_404(Slot, pk=pk)

    if request.method == 'POST':
        form = forms.ReplaceSlotRosterForm(slot, data=request.POST)
        if form.is_valid():
            to_username = form.cleaned_data['to_username']
            to_user = User.objects.get(username__iexact=to_username)
            old_user = slot.user
            slot.user = to_user
            slot.save()

            messages.info(request, "%s replaced with %s on %s" %
                          (get_user_name(old_user),
                           get_user_name(to_user),
                           slot.date.strftime(settings.DEFAULT_DATE_FORMAT)))

            return redirect(reverse('roster.index'))
    else:
        initial = {}
        form = forms.ReplaceSlotRosterForm(slot, initial=initial)

    data['form'] = form
    data['slot'] = slot
    return jingo.render(request, 'roster/replace_slot.html', data)
