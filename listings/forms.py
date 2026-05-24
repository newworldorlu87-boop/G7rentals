from django import forms
from .models import Property, Message


# =========================
# PROPERTY FORM
# =========================
class PropertyForm(forms.ModelForm):

    class Meta:
        model = Property

        fields = [
            'title',
            'description',
            'price',
            'location',
            'property_type',
            'image'
        ]

        widgets = {

            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Property title'
            }),

            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Property description'
            }),

            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Price'
            }),

            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Property location'
            }),

            'property_type': forms.Select(attrs={
                'class': 'form-control'
            }),

            'image': forms.FileInput(attrs={
                'class': 'form-control'
            }),
        }


# =========================
# CONTACT LANDLORD FORM
# =========================
class ContactLandlordForm(forms.ModelForm):

    class Meta:
        model = Message

        fields = [
            'name',
            'email',
            'message'
        ]

        widgets = {

            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your name'
            }),

            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your email'
            }),

            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Write your message...'
            }),
        }


# =========================
# CHAT MESSAGE FORM
# =========================
class MessageForm(forms.ModelForm):

    class Meta:
        model = Message

        fields = ['message']

        widgets = {

            'message': forms.Textarea(attrs={

                'rows': 3,

                'placeholder': 'Type your message...',

                'class': 'chat-input'

            })
        }