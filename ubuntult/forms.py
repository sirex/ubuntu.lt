from django import forms


class ViewForumParams(forms.Form):
    f = forms.IntegerField(min_value=0)


class ViewTopicParams(forms.Form):
    f = forms.IntegerField(min_value=0)
    t = forms.IntegerField(min_value=0)
