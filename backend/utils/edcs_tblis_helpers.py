# nanopore/utils/edcs_tblis_helpers.py
from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_date

def safe_int(val, required=False, field_name=None):
    if val in [None, "", "None", "nan", "NaN"]:
        if required:
            raise ValidationError(f"Missing required value for {field_name}")
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        raise ValidationError(f"Invalid integer value for {field_name}: {val}")

def safe_decimal(val, required=False, field_name=None):
    if val in [None, "", "None", "nan", "NaN"]:
        if required:
            raise ValidationError(f"Missing required value for {field_name}")
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        raise ValidationError(f"Invalid decimal value for {field_name}: {val}")

def parse_date_field(val, required=False, field_name=None):
    if val in [None, "", "None", "nan", "NaN"]:
        if required:
            raise ValidationError(f"Missing required date for {field_name}")
        return None
    parsed = parse_date(str(val))
    if not parsed and required:
        raise ValidationError(f"Invalid date format for {field_name}: {val}")
    return parsed

def get_foreign(obj_class, val, required=False, field_name=None):
    if val in [None, "", "None", "nan", "NaN"]:
        if required:
            raise ValidationError(f"Missing required foreign key for {field_name}")
        return None

    pk = safe_int(val)
    if hasattr(obj_class, "value"):
        obj = obj_class.objects.filter(value=pk).first()
    else:
        obj = obj_class.objects.filter(pk=pk).first()

    if required and not obj:
        raise ValidationError(f"Invalid foreign key for {field_name}: {val}")
    return obj

def split_m2m(obj_class, val, required=False, field_name=None):
    if not val or str(val).lower() in ["none", "nan", ""]:
        if required:
            raise ValidationError(f"Missing required M2M values for {field_name}")
        return []

    val = str(val).replace(";", ",")
    result = []
    for v in str(val).split(","):
        v = v.strip()
        if v:
            obj = get_foreign(obj_class, v, required=True, field_name=field_name)
            if obj:
                result.append(obj)
    return result