from django import forms
from .models import ContactMessage

class ContactMessageForm(forms.ModelForm):
    agree = forms.BooleanField(required=True)

    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'service_type', 'message']