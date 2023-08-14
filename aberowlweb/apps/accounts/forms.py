from django import forms
from django.utils.translation import gettext_lazy as _
from accounts.models import UserProfile
from captcha.fields import ReCaptchaField
from captcha.widgets import ReCaptchaV2Invisible
from allauth.account.forms import LoginForm, SignupForm


class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(
        label=_('First name'),
        max_length=30, )

    last_name = forms.CharField(
        label=_('Last name'),
        max_length=30, )

    class Meta:
        model = UserProfile
        fields = ['first_name', 'last_name', 'birth_date', 'gender']

    def save(self, *args, **kwargs):
        super(UserProfileForm, self).save(*args, **kwargs)
        first_name = self.cleaned_data.get('first_name')
        last_name = self.cleaned_data.get('last_name')
        self.instance.user.first_name = first_name
        self.instance.user.last_name = last_name
        self.instance.user.save()
        return self.instance


class CaptchaSignupForm(SignupForm):
    captcha = ReCaptchaField(widget=ReCaptchaV2Invisible)


class CaptchaLoginForm(LoginForm):
    captcha = ReCaptchaField(widget=ReCaptchaV2Invisible)
