from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Profile
from listings.models import Property


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    user_type = forms.ChoiceField(choices=User.USER_TYPE_CHOICES)

    class Meta:
        model = User
        fields = ['username', 'email', 'user_type', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already exists")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.user_type = self.cleaned_data['user_type']
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'})
    )


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'phone']


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['avatar', 'address', 'city', 'country', 'bio']


# ============================================
# PROPERTY FORM — matches your actual Property model
# ============================================

class PropertyForm(forms.ModelForm):
    amenities = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g., Pool, Gym, Parking, WiFi, AC'
        }),
        help_text="Separate amenities with commas"
    )

    class Meta:
        model = Property
        fields = [
            'title',
            'description',
            'price',
            'address',
            'city',
            'state',
            'zip_code',
            'location',
            'property_type',
            'bedrooms',
            'bathrooms',
            'sqft',
            'image',
            'status',
            'is_available',
            'amenities',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'placeholder': 'e.g., Modern 3-Bedroom Apartment'
            }),
            'description': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Describe the property, neighborhood, and features...'
            }),
            'price': forms.NumberInput(attrs={
                'min': 0,
                'placeholder': 'Monthly rent in Naira'
            }),
            'address': forms.TextInput(attrs={'placeholder': 'Street address'}),
            'city': forms.TextInput(attrs={'placeholder': 'e.g., Abuja'}),
            'state': forms.TextInput(attrs={'placeholder': 'e.g., FCT'}),
            'zip_code': forms.TextInput(attrs={'placeholder': 'e.g., 900001'}),
            'location': forms.TextInput(attrs={
                'placeholder': 'Neighborhood or area (e.g., Wuse, Lekki, Victoria Island)'
            }),
            'bedrooms': forms.NumberInput(attrs={'min': 0}),
            'bathrooms': forms.NumberInput(attrs={'min': 0, 'step': '0.5'}),
            'sqft': forms.NumberInput(attrs={'min': 0, 'placeholder': 'Square footage'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'form-input'
            })

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if price and price < 0:
            raise forms.ValidationError("Price cannot be negative.")
        return price

    def save(self, commit=True):
        property_obj = super().save(commit=False)
        if self.user and not property_obj.pk:
            property_obj.owner = self.user
        if commit:
            property_obj.save()
        return property_obj