from django import forms


class JarFileForm(forms.Form):
    jarfile = forms.FileField(
        label='Select a jar file',
        help_text='max. 42 megabytes'
    )
