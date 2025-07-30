from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class SignUpView(CreateView):
    model = User
    form_class = UserCreationForm
    template_name = 'users/registraion/sign_up.html'
    success_url = reverse_lazy('dashboard:dashboard')  # redirect here after signup
