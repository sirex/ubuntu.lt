from captcha.fields import ReCaptchaField
from captcha.widgets import ReCaptchaV3
from django import forms
from spirit.user.auth.forms import RegistrationForm as SpiritRegistrationForm


class ViewForumParams(forms.Form):
    f = forms.IntegerField(min_value=0)


class ViewTopicParams(forms.Form):
    f = forms.IntegerField(min_value=0)
    t = forms.IntegerField(min_value=0)


class RegistrationForm(SpiritRegistrationForm):
    captcha = ReCaptchaField(widget=ReCaptchaV3)
