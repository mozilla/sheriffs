# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
#
# The contents of this file are subject to the Mozilla Public License Version
# 1.1 (the "License"); you may not use this file except in compliance with
# the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
# for the specific language governing rights and limitations under the
# License.
#
# The Original Code is Mozilla Sheriff Duty.
#
# The Initial Developer of the Original Code is Mozilla Corporation.
# Portions created by the Initial Developer are Copyright (C) 2011
# the Initial Developer. All Rights Reserved.
#
# Contributor(s):
#
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
#
# ***** END LICENSE BLOCK *****

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
from django.shortcuts import render
import forms
from utils.decorators import staff_required
from utils import get_user_name
from models import Slot, Swap
from api import SlotResource


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
            replace_existing = True

            usernames = [x.strip() for x
                         in usernames.splitlines()
                         if x.strip()]
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
                       'until': (last_day +
                         datetime.timedelta(days=1 + len(usernames))),
                       'usernames': '\n'.join(usernames)}

        form = forms.InitializeRosterForm(initial=initial)
    data['users'] = users
    data['form'] = form
    return render(request, 'roster/initialize.html', data)


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
    return render(request, 'roster/replace.html', data)


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
    return render(request, 'roster/index.html', data)


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
    subject = 'Offer to sub Sheriff duty'
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
      'user_name': user_name,
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
    if getattr(settings, 'MAILINGLIST_EMAIL', None):
        tos = [settings.MAILINGLIST_EMAIL]
    else:
        tos = [x[0] for x in (Slot.objects
                              .filter(date__gte=datetime.date.today())
                              .exclude(user__email=request.user.email)
                              .select_related('user')
                              .values_list('user__email')
                              )
               if x]
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
    swap.slot.swap_needed = False
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
    if worked:
        messages.info(request, '%s slot accepted'
                  % swap.slot.date.strftime(settings.DEFAULT_DATE_FORMAT))
    else:
        messages.error(request, 'Unable to send email to %s' %
                       ', '.join(tos))
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
    if worked:
        messages.info(request, '%s slot declined'
                  % swap.slot.date.strftime(settings.DEFAULT_DATE_FORMAT))
    else:
        messages.error(request, 'Unable to send email to %s' %
                       ', '.join(tos))
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
    return render(request, 'roster/replace_slot.html', data)


def api_documentation(request):
    data = {}
    base_url = '%s://%s' % (request.is_secure() and 'https' or 'http',
                            RequestSite(request).domain)
    base_path = '/api/%s' % SlotResource.Meta.api_name
    try:
        random_slot_id = SlotResource.Meta.queryset.order_by('?')[0].pk
    except IndexError:
        random_slot_id = 0
    data['slot_resource_meta'] = SlotResource.Meta
    data['base_url'] = base_url
    data['base_path'] = base_path
    data['api_base_url'] = '%s%s/' % (base_url, base_path)
    data['random_slot_id'] = random_slot_id
    data['slot_base_url'] = ('%s%s/%s/' %
      (base_url, base_path, SlotResource.Meta.resource_name))
    return render(request, 'roster/api_documentation.html', data)


@login_required
def widget_factory(request):  # pragma: no cover
    data = {}

    this_domain = RequestSite(request).domain
    default_options = [
      ('use_date_labels', False,
       'whether to say "Today" or "Thursday" instead of the full date'),
      ('limit', 5, 'number of items to display'),
      ('root_css', '',
       'possible extra CSS added to the root widget element '
       '(e.g. color:#ccc)'),
      ('include_footer', True,
       'include the footer link back to Mozilla Sheriffs Duty'),
      ('host_name', this_domain,
       'this default host name (unlikely to change)'),
      ('root_node_id', 'sheriffs_widget',
       'the ID name of the widget in the DOM tree (unlikely to change)'),
    ]
    default_options_javascript = []
    _longest = max(len('%s %s' % (x, y)) for (x, y, z) in default_options)
    for i, (key, value, comment) in enumerate(default_options):
        if isinstance(value, bool):
            value = str(value).lower()
        elif isinstance(value, basestring):
            value = "'%s'" % value
        comma = (i + 1) < len(default_options) and ',' or ''
        _length = len('%s %s' % (key, value))
        if i == len(default_options) - 1:
            # last option, no comma
            _length -= 1
        whitespace = ' ' * (_longest - _length + 2)
        default_options_javascript.append("%s: %s%s%s// %s" %
          (key, value, comma, whitespace, comment)
        )
    default_options_javascript = '\n'.join(
      '  ' + x for x in default_options_javascript)

    default_code = """
<script>
// all the default options (feel free to delete what you don't change)
var sheriff_options = {
%(default_options_javascript)s
};
</script>
<script src="%(widget_src_url)s"></script>
    """.strip()

    widget_src_url = '//%s' % this_domain
    widget_src_url += '/media/js/widget.js'
    data['default_code'] = default_code % {
      'widget_src_url': widget_src_url,
      'default_options_javascript': default_options_javascript,
    }
    data['count_default_code_lines'] = len(data['default_code'].splitlines())
    data['default_options'] = default_options
    return render(request, 'roster/widget_factory.html', data)
