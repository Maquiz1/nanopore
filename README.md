# DREAM

- FIRST RUN python manage.py seed_roles


<!-- CHECKING DUPLICATE -->

<!--

 python manage.py screening_duplicates -i ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/SCREENING/_2025_09_14/screening_form.csv -o ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/SCREENING/_2025_09_14/duplicates.csv

 -->


<!-- CHECKING PIDS LENGHT -->

<!-- 

 python manage.py screening_pid_lengths -i ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/SCREENING/_2025_09_14/screening_form.csv -o ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/SCREENING/_2025_09_14/screening_pid_lengths.csv

-->



<!-- FINAL COMMAND TO TRANSFORM  -->

<!-- 

python manage.py transform_screening   --input ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/SCREENING/_2025_09_14/screening_form.csv   --output ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/SCREENING/_2025_09_14/screening_ready_values.csv 

-->


<!-- ENROLLMENT -->

<!-- 

python manage.py transform_enrollment   --input ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/ENROLLMENT/_2025_09_14/enrollment_form.csv   --output ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/ENROLLMENT/_2025_09_14/enrollment_ready_values.csv 

-->


<!-- CLINIC -->

<!-- 

python manage.py transform_clinic   --input ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/CLINIC/_2025_09_14/clinic_lab_form.csv   --output ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/CLINIC/_2025_09_14/clinic_ready_values.csv 

-->


<!-- ZONAL -->

<!-- 

python manage.py transform_zonal   --input ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/ZONAL/_2025_09_14/zonal_lab_form.csv   --output ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/ZONAL/_2025_09_14/zonal_ready_values.csv 

-->


<!-- DIAGNOSIS -->

<!-- 

python manage.py transform_diagnosis   --input ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/DIAGNOSIS/_2025_09_14/diagnosis_form.csv   --output ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/DIAGNOSIS/_2025_09_14/diagnosis_ready_values.csv 

-->


<!-- 

python manage.py transform_regimen_changes   --input ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/treatment/_2025_09_14/regimen_form.csv   --output ~/Documents/WORKS/NIMR/DREAM/MIGRATIONS/treatment/_2025_09_14/regimen_ready_values.csv 

-->


