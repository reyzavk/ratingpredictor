from djongo.models import forms
from communicator.models import Ignored

SUPPORTED_ACTION = ('scrape', 'predict', 'ignore', 'unignore', 'query word', 'query ignore')

class ActionForm(forms.Form):

    action = forms.CharField(max_length=50)

    def clean_action(self):
        action = self.cleaned_data.get('action')

        if not action or not action in SUPPORTED_ACTION:
            raise forms.ValidationError(
                    f'{action} is not supported',
                    code='unsupported_action'
                    )

        return action


class SentenceForm(forms.Form):

    sentence = forms.CharField(max_length=500)

class WordForm(forms.ModelForm):

    class Meta:
        model = Ignored
        fields = ('word',)

class URLForm(forms.Form):
    url = forms.URLField()

    def clean_url(self):
        url = self.cleaned_data.get('url')
        if 'tokopedia' not in url:
            raise forms.ValidationError(
                    'currently only support tokopedia',
                    code='url_not_tokopedia'
                    )

        idx = url.find('?')

        if not idx == -1:
            url = url[:idx]

        return url
