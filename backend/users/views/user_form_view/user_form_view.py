from django.views.generic import FormView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model
from users.models import Profile
from users.forms import StaffForm

User = get_user_model()

class StaffCreateUpdateView(FormView):
    template_name = "users/staff/staff_form.html"
    form_class = StaffForm
    success_url = reverse_lazy("users:staff_list")

    def dispatch(self, request, *args, **kwargs):
        self.user_instance = None
        pk = kwargs.get("pk")
        if pk:
            self.user_instance = get_object_or_404(User, pk=pk)
        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        initial = super().get_initial()
        if self.user_instance:
            initial.update({
                "username": self.user_instance.username,
                "email": self.user_instance.email,
                "first_name": self.user_instance.first_name,
                "last_name": self.user_instance.last_name,
                "is_staff": self.user_instance.is_staff,
            })
            # Middle name and description can be stored in profile
            if hasattr(self.user_instance, "profile"):
                profile = self.user_instance.profile
                initial.update({
                    "middle_name": getattr(profile, "middle_name", ""),
                    "description": getattr(profile, "description", ""),
                    "prefix": profile.prefix,
                    "position": profile.position,
                    "site": profile.site,
                    "phone_number": profile.phone_number,
                })
        return initial

    def form_valid(self, form):
        data = form.cleaned_data
        username = data["username"]
        password = data.get("password")
        email = data.get("email")
        first_name = data.get("first_name")
        middle_name = data.get("middle_name")
        last_name = data.get("last_name")
        prefix = data.get("prefix")
        position = data.get("position")
        site = data.get("site")
        phone_number = data.get("phone_number")
        description = data.get("description")
        is_staff = data.get("is_staff", True)

        if self.user_instance:
            # Update existing user
            user = self.user_instance
            user.username = username
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.is_staff = is_staff
            if password:
                user.set_password(password)
            user.save()

            profile, _ = Profile.objects.get_or_create(user=user)
            profile.middle_name = middle_name
            profile.prefix = prefix
            profile.position = position
            profile.site = site
            profile.phone_number = phone_number or None
            profile.description = description or ""
            profile.save()
            messages.success(self.request, f"Staff member '{user.username}' updated successfully!")

        else:
            # Create new user
            if not password:
                form.add_error("password", "Password is required for new user.")
                return self.form_invalid(form)

            if User.objects.filter(username=username).exists():
                form.add_error("username", "Username already exists.")
                return self.form_invalid(form)

            user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
                first_name=first_name,
                last_name=last_name,
                is_staff=is_staff
            )

            Profile.objects.create(
                user=user,
                middle_name=middle_name,
                prefix=prefix,
                position=position,
                site=site,
                phone_number=phone_number or None,
                description=description or ""
            )
            messages.success(self.request, f"Staff member '{username}' created successfully!")

        return super().form_valid(form)

