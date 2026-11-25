from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import Shelf


class LibraLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {"class": "form-control", "autofocus": "autofocus", "placeholder": "Username"}
        )
        self.fields["password"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Password"}
        )



class RegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=False,
        help_text="Optional. We do not send email in this project.",
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
        self.fields["username"].widget.attrs.setdefault("autofocus", "autofocus")
        self.fields["username"].widget.attrs.setdefault(
            "placeholder", "Choose a username"
        )

    def clean_email(self):
        return (self.cleaned_data.get("email") or "").strip().lower()


class ShelfForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        label="Shelf name",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "e.g. Weekend reading"}
        ),
    )

    def __init__(self, *args, user=None, instance=None, **kwargs):
        self.user = user
        self.instance = instance
        super().__init__(*args, **kwargs)
        if instance is not None:
            self.fields["name"].initial = instance.name

    def clean_name(self):
        name = (self.cleaned_data.get("name") or "").strip()
        if not name:
            raise forms.ValidationError("Give your shelf a name.")
        queryset = Shelf.objects.filter(user=self.user, name__iexact=name)
        if self.instance is not None:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise forms.ValidationError("You already have a shelf with that name.")
        return name
