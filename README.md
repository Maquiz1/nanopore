# DREAM

- FIRST RUN python manage.py seed_roles


<!-- CHECKING DUPLICATE -->

<!--

 python manage.py screening_duplicates -i ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/SCREENING/_2025_09_07/screening_form.csv -o ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/SCREENING/_2025_09_07/duplicates.csv

 -->


<!-- CHECKING PIDS LENGHT -->

<!-- 

python manage.py screening_pid_lengths -i ~/Documents/WORKS/NIMR/DREA
M/MIGRATIONS/SCREENING/_2025_09_11/screening_form.csv -o ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/SCREENING/_2025_09_11/screening_pid_length
s.csv-o ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/SCREENING/_2025_09_11/screening_pid_lengths.cs

-->



<!-- FINAL COMMAND TO TRANSFORM  -->

<!-- 

python manage.py transform_screening   --input ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/SCREENING/_2025_09_07/screening_form.csv   --output ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/SCREENING/_2025_09_07/screening_ready_values.csv 

-->


<!-- ENROLLMENT -->

<!-- 

python manage.py transform_enrollment   --input ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/ENROLLMENT/_2025_09_08/nrollment_form.csv   --output ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/ENROLLMENT/_2025_09_08/enro
llment_ready_values.csv 

-->


<!-- CLINIC -->

<!-- 

python manage.py transform_clinic   --input ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/CLINIC/_2025_09_08/clinic_lab_form.csv   --output ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/CLINIC/_2025_09_08/clinic_ready_values.csv 

-->


<!-- ZONAL -->

<!-- 

python manage.py transform_zonal   --input ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/ZONAL/_2025_09_09/clinic_lab_form.csv   --output ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/ZONAL/_2025_09_09/zonal_ready_values.csv 

-->


<!-- DIAGNOSIS -->

<!-- 

python manage.py transform_diagnosis   --input ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/DIAGNOSIS/_2025_09_09/diagnosis_form.csv   --output ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/DIAGNOSIS/_2025_09_09/diagnosis_ready_values.csv 

-->


