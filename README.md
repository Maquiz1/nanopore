# DREAM

- FIRST RUN python manage.py seed_roles


<!-- CHECKING DUPLICATE -->

<!--

python manage.py screening_duplicates -i ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/SCREENING/_2025_09_17/screening_form.csv -o ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/SCREENING/_2025_09_17/duplicates.csv

 -->


<!-- CHECKING PIDS LENGHT -->

<!-- 

python manage.py screening_pid_lengths -i ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/SCREENING/_2025_09_17/screening_form.csv -o ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/SCREENING/_2025_09_17/screening_pid_lengths.csv

-->

<!-- 

python manage.py screening_pid1_and_pid2_checks -i ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/SCREENING/_2025_09_17/screening_form.csv -o ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/SCREENING/_2025_09_17/screening_pid1_and_pid2_checks.csv

-->



<!-- FINAL COMMAND TO TRANSFORM  -->

<!-- 

python manage.py transform_screening   --input ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/SCREENING/_2025_09_17/screening_form.csv   --output ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/SCREENING/_2025_09_17/screening_ready_values.csv 

-->


<!-- ENROLLMENT -->

<!-- 

python manage.py transform_enrollment   --input ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/ENROLLMENT/_2025_09_17/enrollment_form.csv   --output ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/ENROLLMENT/_2025_09_17/enrollment_ready_values.csv 

-->


<!-- CLINIC -->

<!-- 

python manage.py transform_clinic   --input ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/CLINIC/_2025_09_17/clinic_lab_form.csv   --output ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/CLINIC/_2025_09_17/clinic_ready_values.csv 

-->


<!-- ZONAL -->

<!-- 

python manage.py transform_zonal   --input ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/ZONAL/_2025_09_17/zonal_lab_form.csv   --output ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/ZONAL/_2025_09_17/zonal_ready_values.csv 

-->


<!-- DIAGNOSIS -->

<!-- 

python manage.py transform_diagnosis   --input ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/DIAGNOSIS/_2025_09_17/diagnosis_form.csv   --output ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/DIAGNOSIS/_2025_09_17/diagnosis_ready_values.csv 

-->

<!-- REGIMES CHANGES -->

<!-- 

python manage.py transform_regimen_changes   --input ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/treatment/_2025_09_14/regimen_form.csv   --output ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/treatment/_2025_09_14/regimen_ready_values.csv 

-->








<!-- It looks like you’re trying to use `pdfkit` in Python to generate PDFs. That line itself is fine, but to use `pdfkit` successfully, you need to make sure **two things** are in place: -->




<!-- implement **PDF export** using **WeasyPrint**, which works nicely with Django templates to generate styled PDFs. I’ll update your `ExportRecordsView` to support both **Excel (CSV)** and **PDF** exports. -->

---

### **1️⃣ Install WeasyPrint**

Run in your environment:

```bash
pip install weasyprint
```

<!-- > Note: WeasyPrint may require system dependencies like `libpango`, `cairo`, `gdk-pixbuf`, etc. On Ubuntu/Debian: -->

```bash
sudo apt install libpango1.0-0 libcairo2 libgdk-pixbuf2.0-0 libffi-dev
```

---

✅ **Now you have:**

1. Excel (CSV) export with current filters.
2. PDF export via WeasyPrint with proper table formatting.
3. Compatible with **zones, sites, months, and substudy filters**.

---






---

### 1️⃣ Install `pdfkit`

```bash
pip install pdfkit
```

---

### 2️⃣ Install `wkhtmltopdf`

`pdfkit` is just a wrapper; it needs `wkhtmltopdf` to convert HTML to PDF.

**On Ubuntu/Debian:**

```bash
sudo apt update
sudo apt install wkhtmltopdf
```

**On Windows:**

* Download the installer from [wkhtmltopdf.org](https://wkhtmltopdf.org/downloads.html)
* Add the installed directory to your `PATH`.

---

### 3️⃣ Configure `pdfkit` (optional)

If `wkhtmltopdf` is not in your PATH, you can specify it explicitly:

```python
import pdfkit

path_wkhtmltopdf = '/usr/local/bin/wkhtmltopdf'  # adjust path
config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)

pdfkit.from_url('https://example.com', 'output.pdf', configuration=config)
```

---

✅ After that, you can generate PDFs from HTML strings, files, or URLs:

```python
pdfkit.from_string('<h1>Hello World</h1>', 'hello.pdf')
pdfkit.from_file('template.html', 'output.pdf')
```

---

If you want, I can also show a **Django view example that generates a PDF from a template using `pdfkit`**, which is often the most common use case. Do you want me to do that?

