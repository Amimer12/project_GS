from django import forms
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from .models import Gestionnaire
from Products.models import Boutique

User = get_user_model()
class GestionnaireCreationForm(forms.ModelForm):
    username = forms.CharField(label="Nom d'utilisateur")
    email = forms.EmailField(label="Email")
    password1 = forms.CharField(label="Mot de passe", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirmez le mot de passe", widget=forms.PasswordInput)
    boutique = forms.ModelMultipleChoiceField(
        queryset=Boutique.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Boutiques"
    )

    class Meta:
        model = Gestionnaire
        fields = ("username", "email", "password1", "password2", "boutique")

    def clean_username(self):
        username = self.cleaned_data.get("username")
        # Only validate for new instances, not updates
        if not self.instance.pk and User.objects.filter(username=username).exists():
            raise forms.ValidationError("Ce nom d'utilisateur est déjà utilisé.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")
        # Only validate for new instances, not updates
        if not self.instance.pk and User.objects.filter(email=email).exists():
            raise forms.ValidationError("Cet email est déjà utilisé.")
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        return password2

    def save(self, commit=True):
        # Create or get the user
        user = User(
            username=self.cleaned_data["username"],
            email=self.cleaned_data["email"],
            is_staff=True,
        )
        user.set_password(self.cleaned_data["password1"])
        user.save()

        # Assign group
        from django.contrib.auth.models import Group
        try:
            group = Group.objects.get(name="Gestionnaire")
            user.groups.add(group)
        except Group.DoesNotExist:
            pass

        # Use the regular ModelForm save pattern
        gestionnaire = super().save(commit=False)
        gestionnaire.user = user
        if commit:
            gestionnaire.save()
            self.save_m2m()  # ✅ Now safe to call
        return gestionnaire

class GestionnaireChangeForm(forms.ModelForm):
    username = forms.CharField(label="Nom d'utilisateur")
    email = forms.EmailField(label="Email")
    first_name = forms.CharField(label="Prénom", required=False)
    last_name = forms.CharField(label="Nom", required=False)
    is_staff = forms.BooleanField(label="Authorisé", required=False)
    boutique = forms.ModelMultipleChoiceField(
        queryset=Boutique.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Boutiques"
    )

    class Meta:
        model = Gestionnaire
        fields = ("boutique",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            user = self.instance.user
            self.fields['username'].initial = user.username
            self.fields['email'].initial = user.email
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['is_staff'].initial = user.is_staff

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exclude(pk=self.instance.user.pk).exists():
            raise forms.ValidationError("Cet email est déjà utilisé.")
        return email

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if User.objects.filter(username=username).exclude(pk=self.instance.user.pk).exists():
            raise forms.ValidationError("Ce nom d'utilisateur est déjà utilisé.")
        return username

    def save(self, commit=True):
        gestionnaire = super().save(commit=False)
        user = gestionnaire.user
        user.username = self.cleaned_data["username"]
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.is_staff = self.cleaned_data["is_staff"]
        user.save()

        if commit:
            gestionnaire.save()
            self.save_m2m()
        return gestionnaire
