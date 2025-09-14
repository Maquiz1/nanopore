from django import forms
from django.core.exceptions import ValidationError
from nanopore.models import ZonalLaboratory
from options.models import YesNo,SampleAppearance
from common.labels.laboratory.zonal.zonal_labels import ZONAL_LABELS   # ✅ import from core app

class ZonalLaboratoryForm(forms.ModelForm):
    class Meta:
        model = ZonalLaboratory
        fields = [
            "screening", 
            # Specimen Receipt
            "date_sputum_received", "appearance", "sample_volume", "unique_lab_no",
            
            # Culture
            "culture_performed", "culture_method", "microscopy_type", "microscopy_date", "microscopy_results",
            
            # LJ Results
            "lj_inoculation_date", "lj_results_date", "lj_results",
            
            # MGIT Results
            "mgit_inoculation_date", "mgit_results_date", "mgit_results",
            
            # Culture Isolate
            "culture_isolate", "isolate_date",
            
            # Phenotypic DST
            
            "phenotypic_performed", "phenotypic_date_performed", "phenotypic_date_results",
            
            # Phenotypic DST RESULTS
            "rifampicin", "isoniazid", "levofloxacin", "moxifloxacin", "bedaquiline",
            "linezolid", "clofazimine", "cycloserine", "terizidone", "ethambutol",
            "delamanid", "pyrazinamide", "imipenem", "cilastatin", "meropenem",
            "amikacin", "streptomycin", "ethionamide", "prothionamide", "para_aminosalicylic_acid",
            
            # Xpert XDR
            "xpert_xdr_performed", "xpert_xdr_date_performed",
            
            # Xpert XDR RESULTS
            "xpert_xdr_isoniazid",
            "xpert_xdr_fluoroquinolones",
            "xpert_xdr_amikacin",
            "xpert_xdr_kanamycin",
            "xpert_xdr_capreomycin",
            "xpert_xdr_ethionamide",
           
            # First-Line LPA
            "first_line_lpa",
            "first_line_lpa_date",
            "first_line_drugs",
            "lpa1_mtb",
            "lpa1_rif",
            "lpa1_inh",

            # Second-Line LPA
            "second_line_lpa",
            "second_line_lpa_date",
            "second_line_drugs",
            "lpa2_mtb",
            "lpa2_rfluoroquinolones",
            "lpa2_aminoglycosides",
            "lpa2_kanamycin",
            
            
            # Nanopore sequencing
            "nanopore_done",
            "sequencing_results",
            "epi_to_me",
            "epi_to_me_version",
            
            # Nanopore sequencing Results

            "nano_amikacin",
            "nano_bedaquiline",
            "nano_capreomycin",
            "nano_clofazimine",
            "nano_delamanid",
            "nano_ethambutol",
            "nano_ethionamide",
            "nano_isoniazid",
            "nano_kanamycin",
            "nano_levofloxacin",
            "nano_linezolid",
            "nano_moxifloxacin",
            "nano_pretomanid",
            "nano_pyrazinamide",
            "nano_rifampicin",
            "nano_streptomycin",
            
            # Additional Remarks
            "remarks",

        ]
        # fields = TB_LABELS.keys()
        labels = ZONAL_LABELS
        
        widgets = {
            "screening": forms.HiddenInput(),
            "culture_method": forms.CheckboxSelectMultiple(),
            
            # Specimen Receipt
            "appearance": forms.Select(attrs={"class": "form-select"}),
            "date_sputum_received": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "sample_volume": forms.NumberInput(attrs={"class": "form-control"}),
            "unique_lab_no": forms.TextInput(attrs={"class": "form-control"}),
            
            # Culture
            "culture_performed": forms.Select(attrs={"class": "form-select"}),
            "microscopy_type": forms.Select(attrs={"class": "form-select"}),
            "microscopy_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "microscopy_results": forms.Select(attrs={"class": "form-select"}),
            
            # LJ Results
            "lj_inoculation_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "lj_results_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "lj_results": forms.Select(attrs={"class": "form-select"}),
            
            # MGIT Results
            "mgit_inoculation_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "mgit_results_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "mgit_results": forms.Select(attrs={"class": "form-select"}),
            
            # Culture Isolate
            "culture_isolate": forms.Select(attrs={"class": "form-select"}),
            "isolate_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            
            # Phenotypic DST
            "phenotypic_performed": forms.Select(attrs={"class": "form-select"}),
            "phenotypic_date_performed": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "phenotypic_date_results": forms.Select(attrs={"class": "form-select"}),
            
            # Phenotypic DST RESULTS
            "rifampicin": forms.Select(attrs={"class": "form-select"}),
            "isoniazid": forms.Select(attrs={"class": "form-select"}),
            "levofloxacin": forms.Select(attrs={"class": "form-select"}),
            "moxifloxacin": forms.Select(attrs={"class": "form-select"}),
            "bedaquiline": forms.Select(attrs={"class": "form-select"}),
            "linezolid": forms.Select(attrs={"class": "form-select"}),
            "clofazimine": forms.Select(attrs={"class": "form-select"}),
            "cycloserine": forms.Select(attrs={"class": "form-select"}),
            "terizidone": forms.Select(attrs={"class": "form-select"}),
            "ethambutol": forms.Select(attrs={"class": "form-select"}),
            "delamanid": forms.Select(attrs={"class": "form-select"}),
            "pyrazinamide": forms.Select(attrs={"class": "form-select"}),
            "imipenem": forms.Select(attrs={"class": "form-select"}),
            "cilastatin": forms.Select(attrs={"class": "form-select"}),
            "meropenem": forms.Select(attrs={"class": "form-select"}),
            "amikacin": forms.Select(attrs={"class": "form-select"}),
            "streptomycin": forms.Select(attrs={"class": "form-select"}),
            "ethionamide": forms.Select(attrs={"class": "form-select"}),
            "prothionamide": forms.Select(attrs={"class": "form-select"}),
            "para_aminosalicylic_acid": forms.Select(attrs={"class": "form-select"}),
            
            # Xpert XDR
            "xpert_xdr_performed": forms.Select(attrs={"class": "form-select"}),
            "xpert_xdr_date_performed": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            
            # Xpert XDR RESULTS
            "xpert_xdr_isoniazid": forms.Select(attrs={"class": "form-select"}),
            "xpert_xdr_fluoroquinolones": forms.Select(attrs={"class": "form-select"}),
            "xpert_xdr_amikacin": forms.Select(attrs={"class": "form-select"}),
            "xpert_xdr_kanamycin": forms.Select(attrs={"class": "form-select"}),
            "xpert_xdr_capreomycin": forms.Select(attrs={"class": "form-select"}),
            "xpert_xdr_ethionamide": forms.Select(attrs={"class": "form-select"}),
            
            # First-Line LPA
            "first_line_lpa": forms.Select(attrs={"class": "form-select"}),
            "first_line_lpa_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "first_line_drugs": forms.CheckboxSelectMultiple(),
            "lpa1_mtb": forms.Select(attrs={"class": "form-select"}),
            "lpa1_rif": forms.Select(attrs={"class": "form-select"}),
            "lpa1_inh": forms.CheckboxSelectMultiple(),
            
            
            # Second-Line LPA            
            "second_line_lpa": forms.Select(attrs={"class": "form-select"}),
            "second_line_lpa_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "second_line_drugs": forms.CheckboxSelectMultiple(),
            "lpa2_mtb": forms.Select(attrs={"class": "form-select"}),
            "lpa2_rfluoroquinolones": forms.Select(attrs={"class": "form-select"}),
            "lpa2_aminoglycosides": forms.Select(attrs={"class": "form-select"}),
            "lpa2_kanamycin": forms.Select(attrs={"class": "form-select"}),
            
            
            # Nanopore sequencing
            "nanopore_done": forms.Select(attrs={"class": "form-select"}),
            "sequencing_results": forms.Select(attrs={"class": "form-select"}),
            "epi_to_me": forms.Select(attrs={"class": "form-select"}),
            "epi_to_me_version": forms.TextInput(attrs={"class": "form-control"}),
            
            
            # Nanopore sequencing Results
            "nano_amikacin": forms.Select(attrs={"class": "form-select"}),
            "nano_bedaquiline": forms.Select(attrs={"class": "form-select"}),
            "nano_capreomycin": forms.Select(attrs={"class": "form-select"}),
            "nano_clofazimine": forms.Select(attrs={"class": "form-select"}),
            "nano_delamanid": forms.Select(attrs={"class": "form-select"}),
            "nano_ethambutol": forms.Select(attrs={"class": "form-select"}),
            "nano_ethionamide": forms.Select(attrs={"class": "form-select"}),
            "nano_isoniazid": forms.Select(attrs={"class": "form-select"}),
            "nano_kanamycin": forms.Select(attrs={"class": "form-select"}),
            "nano_levofloxacin": forms.Select(attrs={"class": "form-select"}),
            "nano_linezolid": forms.Select(attrs={"class": "form-select"}),
            "nano_moxifloxacin": forms.Select(attrs={"class": "form-select"}),
            "nano_pretomanid": forms.Select(attrs={"class": "form-select"}),
            "nano_pyrazinamide": forms.Select(attrs={"class": "form-select"}),
            "nano_rifampicin": forms.Select(attrs={"class": "form-select"}),
            "nano_streptomycin": forms.Select(attrs={"class": "form-select"}),
            
            "remarks": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            
        }


    def __init__(self, *args, **kwargs):
        screening_instance = kwargs.pop("screening_instance", None)
        super().__init__(*args, **kwargs)
        if screening_instance:
            self.fields["screening"].initial = screening_instance.pk
        # Keep readonly display in template
        self.readonly_screening = screening_instance

    def clean(self):
        cleaned_data = super().clean()
        screening = cleaned_data.get("screening")
        if screening and self.instance.pk is None:
            if hasattr(screening, "zonal_laboratory"):
                raise ValidationError(f"This screening {screening} already has a zonal lab record.")
        return cleaned_data
