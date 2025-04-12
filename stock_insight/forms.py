from django import forms
from .models import News

# creating form from existing table in database

# class LoginForm(forms.Form):
#     username = forms.CharField()
#     password = forms.CharField(widget=forms.PasswordInput)
#     remember_me = forms.BooleanField(required=False)

class NewsForm(forms.ModelForm):
    class Meta:
        # store database variables in model 
        model=News
        fields='__all__'
        widgets = {
            'head': forms.TextInput(attrs={'class': 'form-control'}),
            'sub_head': forms.TextInput(attrs={'class': 'form-control'}),
            'image_link': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'type': 'date'}),  # Ensures a date picker
            # 'sentiment': forms.TextInput(attrs={'class': 'form-select'}),
            
        }
        # if you want specific fileds only like head and subhead then use (fields=['head','sub_head']) 
        
    # # Adding validation
    def clean_head(self):
        head=self.cleaned_data.get('head')
        if len(head)<5:
            raise forms.ValidationError('Head can not be less than 5 words')
        return head
    
#creating review form
class ReviewForm(forms.Form):
    EXPERIENCE_CHOICES = [     
                            (1, 'Bad'),
                            (2, 'Average'),
                            (3, 'Decent'),
                            (4, 'Good'),
                            (5, 'Excellent'),
                            ]
    fname = forms.CharField(label='First Name', max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}), label_suffix='')
    lname = forms.CharField(label='Last Name', max_length=50, widget=forms.TextInput(attrs={'class': 'form-control'}), label_suffix='')
    email = forms.EmailField(label='Email Id', max_length=254, widget=forms.EmailInput(attrs={'class': 'form-control'}), label_suffix='')
    comment = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control'}), label_suffix='')
    
    exp = forms.ChoiceField(
        label="Rating",
        choices=[(str(i), str(i)) for i in range(1, 6)],  # Creates choices 1-5
        widget=forms.RadioSelect,  # Use radio buttons
        required=True,
    )
