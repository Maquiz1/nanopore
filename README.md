# DREAM

- FIRST RUN python manage.py seed_roles


<!-- CHECKING DUPLICATE -->

<!--

python manage.py screening_duplicates -i ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/SCREENING/_2025_10_13/screening_form.csv -o ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/SCREENING/_2025_10_13/duplicates.csv

 -->


<!-- CHECKING PIDS LENGHT -->

<!-- 

python manage.py screening_pid_lengths -i ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/SCREENING/_2025_10_13/screening_form.csv -o ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/SCREENING/_2025_10_13/screening_pid_lengths.csv

-->

<!-- 

python manage.py screening_pid1_and_pid2_checks -i ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/SCREENING/_2025_10_13/screening_form.csv -o ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/SCREENING/_2025_10_13/screening_pid1_and_pid2_checks.csv

-->

<!-- UPDATING AGE,SEX AND DOB -->

<!--

python manage.py update_screening_age_sex_dob \
  --screening_csv ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/SCREENING/_2025_10_13/screening_form.csv \
  --enrollment_csv ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/ENROLLMENT/_2025_10_13/enrollment_form.csv \
  --output_csv ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/SCREENING/_2025_10_13/screening_updated_form.csv
 
  
-->



<!-- FINAL COMMAND TO TRANSFORM  -->

<!-- 

python manage.py transform_screening   --input ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/SCREENING/_2025_10_13/screening_updated_form.csv   --output ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/SCREENING/_2025_10_13/screening_ready_values.csv 

-->


<!-- ENROLLMENT -->

<!-- 

python manage.py transform_enrollment   --input ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/ENROLLMENT/_2025_10_13/enrollment_form.csv   --output ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/ENROLLMENT/_2025_10_13/enrollment_ready_values.csv 

-->


<!-- CLINIC -->

<!-- 

python manage.py transform_clinic   --input ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/CLINIC/_2025_10_13/clinic_lab_form.csv   --output ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/CLINIC/_2025_10_13/clinic_ready_values.csv 

-->


<!-- ZONAL -->

<!-- 

python manage.py transform_zonal   --input ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/ZONAL/_2025_10_13/zonal_lab_form.csv   --output ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/ZONAL/_2025_10_13/zonal_ready_values.csv 

-->


<!-- DIAGNOSIS -->

<!-- 

python manage.py transform_diagnosis   --input ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/DIAGNOSIS/_2025_10_13/diagnosis_form.csv   --output ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/DIAGNOSIS/_2025_10_13/diagnosis_ready_values.csv 

-->

<!-- REGIMES CHANGES -->

<!-- 

python manage.py transform_regimen_changes   --input ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/treatment/_2025_10_13/regimen_form.csv   --output ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/treatment/_2025_10_13/regimen_ready_values.csv 

-->


<!-- Back Up  -->
<!-- 

pg_dump -U username -h localhost -p 5432 -Fc nanopore > ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/Back_Up/_2025_10_13/nanopore_2025_10_13.dump

-->


<!-- pg_restore -U myuser -h localhost -p 5432 -d nanopore_restored ~/Documents/WORKS/nanopore.dump
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




MOBILE APP


📱 Nanopore Mobile Starter (React Native + DRF)
1. ✅ Setup React Native Project

Run this on your dev machine:

To create a new Expo project, run the following in your terminal:

npx create-expo-app nanopore-mobile

OR 

npx create-expo-app@latest


Choose the blank (JavaScript) template.

2. ✅ To start the development server, run the following command:TO Terminal

cd nanopore-mobile

npx expo start

3. ✅ Project Structure
nanopore-mobile/
 ├── App.js
 ├── api/
 │    └── client.js
 ├── screens/
 │    ├── LoginScreen.js
 │    ├── DashboardScreen.js
 │    └── ScreeningFormScreen.js
 └── utils/
      └── auth.js

4. npm run reset-project

This command will move the existing files in app to app-example, then create a new app directory with a new index.tsx file.




EAS CLI
EAS CLI is used to log in to your Expo account and compile your app using different EAS services such as Build, Update, or Submit. You can also use this tool to:

Publish your app to the app stores
Create a development, preview, or production build of your app
Create over-the-air (OTA) updates
Manage your app credentials
Create an ad hoc provisioning profile for an iOS device
To use EAS CLI, you need to install it globally on your local machine by running the command:

Terminal

Copy

npm install -g eas-cli
You can use eas --help in your terminal window to learn more about the available commands. For a complete reference, see eas-cli npm page.

Expo Doctor
Expo Doctor is a command line tool used to diagnose issues in your Expo project. To use it, run the following command in your project's root directory:

Terminal

Copy

npx expo-doctor
