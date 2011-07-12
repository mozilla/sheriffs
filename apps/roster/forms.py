import datetime
from django.contrib.auth.models import User
from django.conf import settings
from django import forms
from utils import get_user_name
from models import Slot


class BaseForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super(BaseForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            if isinstance(self.fields[field], forms.fields.DateField):
                klass = self.fields[field].widget.attrs.get('class')
                if klass:
                    klass += ' date'
                else:
                    klass = 'date'
                self.fields[field].widget.attrs['class'] = klass
                self.fields[field].input_formats = \
                  [settings.DEFAULT_DATE_FORMAT]
                self.fields[field].widget.format = settings.DEFAULT_DATE_FORMAT


class InitializeRosterForm(BaseForm):
    starting = forms.fields.DateField()
    until = forms.fields.DateField()
    usernames = forms.fields.CharField(widget=forms.widgets.Textarea())


class InsertRosterForm(BaseForm):
    starting = forms.fields.DateField()
    username = forms.fields.CharField()

    def clean_username(self):
        value = self.cleaned_data['username'].strip()
        try:
            value = User.objects.get(username__iexact=value).username
        except User.DoesNotExist:
            raise forms.ValidationError("Unrecognized user")
        return value


class ReplaceRosterForm(BaseForm):
    from_username = forms.fields.ChoiceField()
    to_username = forms.fields.ChoiceField()
    starting = forms.fields.DateField(required=False)
    until = forms.fields.DateField(required=False)

    def __init__(self, *args, **kwargs):
        super(ReplaceRosterForm, self).__init__(*args, **kwargs)

        choices = []
        for slot in (Slot.objects
          .filter(date__gte=datetime.date.today())
          .select_related('user')
          .order_by('user__first_name', 'user__username')):
            if slot.user.username not in [x[0] for x in choices]:
                choices.append((slot.user.username, get_user_name(slot.user)))
        self.fields['from_username'].choices = choices

        choices = []
        for user in (User.objects.filter(is_active=True)
          .order_by('first_name', 'username')):
            choices.append((user.username, get_user_name(user)))
        self.fields['to_username'].choices = choices


class ReplaceSlotRosterForm(BaseForm):
    to_username = forms.fields.ChoiceField()

    def __init__(self, slot, *args, **kwargs):
        super(ReplaceSlotRosterForm, self).__init__(*args, **kwargs)
        choices = []
        for user in (User.objects.filter(is_active=True)
          .exclude(pk=slot.user_id)
          .order_by('first_name', 'username')):
            choices.append((user.username, get_user_name(user)))
        self.fields['to_username'].choices = choices
