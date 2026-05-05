from django import forms
from .models import Inscription

class InscriptionForm(forms.ModelForm):
    class Meta:
        model = Inscription
        exclude = ['created_at', 'annee_academique']
        widgets = {
            'dob': forms.DateInput(attrs={'type': 'date', 'class': 'field-input'}),
            'last_name': forms.TextInput(attrs={'oninput': 'this.value = this.value.toUpperCase()', 'placeholder': 'Ex : DUPONT', 'class': 'field-input'}),
            'first_name': forms.TextInput(attrs={'oninput': 'this.value = this.value.toUpperCase()', 'placeholder': 'Ex : MARIE', 'class': 'field-input'}),
            'pob': forms.TextInput(attrs={'oninput': 'this.value = this.value.toUpperCase()', 'class': 'field-input'}),
            'nationalite': forms.TextInput(attrs={'oninput': 'this.value = this.value.toUpperCase()', 'class': 'field-input'}),
            'sexe': forms.Select(attrs={'class': 'field-select'}),
            'target_etablissement': forms.Select(attrs={'class': 'field-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if not field.widget.attrs.get('class'):
                field.widget.attrs['class'] = 'field-input'
            if field.required:
                field.label = f"{field.label} *"
