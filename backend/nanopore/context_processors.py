from nanopore.models.system_control import SystemControl

def system_controls(request):
    """
    Injects the global SystemControl instance into all templates.
    """
    # Use the first one or create it if it doesn't exist.
    control = SystemControl.objects.first()
    if not control:
        try:
            control = SystemControl.objects.create()
        except Exception:
            # Fallback for migrations or db issues
            control = SystemControl(enable_form_submissions=True, enable_new_screening=True)
            
    return {'system_control': control}
