# DREAM – Nanopore: System User Flow

DREAM is a Django web application (`backend/`) for the Nanopore TB study. It records each
participant's journey from screening, through clinic and zonal laboratory testing, to diagnosis
and treatment, and gives reviewers dashboards, data-quality queries and exports.

> `frontend/` is empty and `nanopore-mobile/` is an Expo (React Native) starter app with only
> home and settings tabs. All real user flows are served by the Django backend templates.

---

## 1. Setup (first run)

```bash
python manage.py migrate
python manage.py seed_roles   # creates site types, site levels, user groups and permissions
```

`seed_roles` creates:

| Seeded item | Values |
|---|---|
| Site types | Clinic, Laboratory |
| Site levels | Local, Zonal, National |
| Groups | NURSE, CLINICIAN, LABORATORY_TECHNICIAN, ADMIN, REVIEWER |

Locations form a hierarchy: **Country → Zone → Region → District → Site**. Each site has a
`pid_prefix` that is used to build participant IDs.

---

## 2. Account and access flow

```
Sign up ──► account created (inactive) ──► activation e-mail ──► user clicks link ──► active
                                                                                         │
Login ──► "/" redirects ──► Dashboard  (anonymous users are sent to the login page) ◄────┘
```

1. **Sign up** (`/users/`): the account is created with `is_active = False` and an activation
   link is e-mailed. The activation e-mail can be resent.
2. **Admin assignment**: an admin gives the user a **group** (role) and assigns **sites** and/or
   **zones** on their Profile.
3. **Login**: `/` sends logged-in users to `/dashboard/` and everyone else to the login page.

### What each role can do

A user can hold **several roles**, and their rights are the union of all of them.
For example, LABORATORY_TECHNICIAN + DATA_SPECIALIST can edit every form.

| Role | Can edit | Can view (read-only) | Reports / Exports |
|---|---|---|---|
| NURSE / CLINICIAN | Screening, Enrollment, Clinic Lab, Diagnosis, Regimen | – | – |
| LABORATORY_TECHNICIAN | Zonal Lab, EDCS/TB-LIS | Screening (to look up the PID) | – |
| DATA_SPECIALIST | All forms (this is how data-quality queries get resolved) | – | Yes, plus TB-LIS raw upload |
| REVIEWER | – | All forms | Yes |
| ADMIN | All forms | – | Yes, plus model export, snapshots, system controls |
| Superuser | Everything, including bulk CSV uploads | | |

### Which records a user sees (assignment)

- **Zone assigned:** every site in that zone. A zone assignment overrides any site assignment.
- **Sites only:** exactly those sites. The one exception is a LABORATORY_TECHNICIAN assigned to a
  **zonal-level** lab site, who sees the whole zone, or a **national-level** lab site, who sees
  the whole country. This is because lab results belong to the clinic where the participant
  was screened, not to the lab.
- **ADMIN, REVIEWER, superuser:** every record.
- **No role, or no assignment:** no records.
- Raw TB-LIS rows have no site, so only ADMIN and REVIEWER see them.

The same rules apply to lists, record pages, reports, data-quality queries, dashboards and
exports. Opening a record outside your scope by URL returns 404. Opening a form your roles
don't cover returns 403.

All of these rules live in `backend/utils/access.py`, and views enforce them through
`backend/utils/access_mixins.py`.

---

## 3. Participant (data-entry) flow

Every form after Screening is linked one-to-one to a **Screening** record through the PID.

```
            ┌──────────────┐
            │  SCREENING   │  Nurse / Clinician
            │  PID created │
            └──────┬───────┘
                   │ eligible?
         no ◄──────┴──────► yes
   (stops here,             │
    counted in reports)     ▼
                     ┌──────────────┐
                     │  ENROLLMENT  │  Nurse / Clinician (symptoms, history…)
                     └──────┬───────┘
                            ▼
                     ┌──────────────┐
                     │  CLINIC LAB  │  Nurse / Clinician (Xpert MTB/RIF at the clinic)
                     └──────┬───────┘      └─► determines the Substudy (2 or 4)
                            ▼
                     ┌──────────────┐
                     │  ZONAL LAB   │  Lab technician (culture, DST, LPA, Xpert XDR,
                     └──────┬───────┘                   Nanopore sequencing)
                            ▼
                     ┌──────────────┐
                     │  DIAGNOSIS   │  Nurse / Clinician (TB outcome)
                     └──────┬───────┘
                            ▼
                     ┌──────────────┐
                     │ REGIMEN      │  Clinician (zero or more treatment changes)
                     │ CHANGES      │
                     └──────────────┘
```

### 3.1 Screening (`/nanopore/screenings/`)
- The user picks the **site** and enters `pid1` / `pid2` (three digits each).
  The system builds `pid = site.pid_prefix + pid1`, which must be unique.
  `/nanopore/check-pid/` checks whether a PID already exists.
- The screening date must be between **20 Jan 2025** and today.
- **Eligibility** is calculated automatically when the record is saved:
  - Consent = Yes, unable to understand = No, not willing = No
  - **and** age ≥ 18 = Yes, can produce a respiratory sample = Yes
  - **and** for the *Dar es Salaam* zone, presenting symptoms = Yes;
    for every other zone, GeneXpert confirmation = Yes

### 3.2 Enrollment (`/nanopore/enrollments/`)
Clinical baseline for eligible participants (cough ≥ 2 weeks, weight loss and so on).

### 3.3 Clinic Laboratory (`/nanopore/clinic-labs/`)
Clinic-level Xpert MTB/RIF results. These results assign the participant to a substudy:
- **Substudy 2**: Xpert done, MTB detected
- **Substudy 4**: Xpert done and MTB not detected or invalid, **or** Xpert not done
- **Uncategorized**: no Xpert information yet

### 3.4 Zonal Laboratory (`/nanopore/zonal-labs/`)
Entered by lab technicians: sputum receipt, appearance, culture (LJ / MGIT), phenotypic DST
for each drug, Xpert XDR, LPA (first and second line), and Nanopore sequencing results with
resistance calls for each drug.

**EDCS / TB-LIS** (`/nanopore/edcs-tblis/`): zonal lab data can also be bulk-imported from
TB-LIS exports. These imports run as background **Celery** tasks with status polling and the
option to revoke a task, and they produce discrepancy reports that can be downloaded.

### 3.5 Diagnosis (`/nanopore/diagnoses/`)
Final TB outcome. A diagnosis with an outcome code from 1 to 6 marks the participant as
**completed**.

### 3.6 Regimen Changes (`/nanopore/regimen/`)
Treatment changes and the reasons for them. A participant can have several.

### Common actions on every form
List (with filters for zone, site, PID, date range and lab number) → View detail → Create /
Update → Delete, plus **CSV upload** for bulk entry and a field **audit history**.

---

## 4. Tracking progress: Form Status (`/nanopore/form-status/`)

One list shows each participant and which forms they have, with quick views:

| View | Meaning |
|---|---|
| `screened/` | Every screening record |
| `eligible/` | Records where `eligible = True` |
| `enrolled/` | Records that have an Enrollment |
| `completed/` | Records with a Diagnosis outcome from 1 to 6 |

It can also be filtered by substudy (2, 4 or uncategorized), zone, site, PID and date.

---

## 5. Monitoring, reporting and data quality

| Area | URL | Purpose |
|---|---|---|
| Dashboard | `/dashboard/` | Landing page with graphs and progress against targets |
| Reports | `/reports/summary/`, `forms/`, `enrollment-summary/`, `eligibility_summary/`, `completed_study_summary/`, `substudy/<name>/` | Summary tables by zone and site |
| Records | `/reports/records/completed/`, `records/in-progress/`, `zone/<id>/<status>/`, `site/<id>/<status>/` | Drill down into records |
| Data quality | `/reports/data-quality/all-issues/`, `/reports/queries/` | Missing forms and field-level issues (snapshots are built by `snapshot_*_dq` commands) |
| Exports | `/reports/download/<model>/`, `/nanopore/screenings/download/…` | CSV/XLSX exports, run as background tasks where the data is large |
| Manuals | `/manuals/` | Study documents and SOPs |

---

## 6. Administration

- **System Controls** (`/nanopore/system-controls/`) are global switches:
  - `enable_form_submissions`: when off, the Submit button is disabled on every form
    (for example to freeze data).
  - `enable_new_screening`: when off, the "New Screening" button is hidden.
- **Master data** (`/nanopore/master-data/`): lookup lists such as Yes/No and result options.
- **Locations** (`/locations/`): manage zones, regions, districts and sites.
- **Users** (`/users/`): list, create, edit and delete users, and assign roles, sites and zones.
- **Data migration**: the management commands `screening_duplicates`, `screening_pid_lengths`,
  `screening_pid1_and_pid2_checks`, `update_screening_age_sex_dob`, `transform_*` and
  `merge_clinic_*` clean legacy CSVs and load them (see the root `README.md`).

---

## 7. End-to-end summary

1. The admin seeds roles, sets up locations, approves users and assigns their sites.
2. A nurse or clinician screens a participant, and the system creates the PID and decides
   eligibility.
3. For eligible participants they complete **Enrollment** and **Clinic Lab**, which sets the
   substudy.
4. A lab technician completes the **Zonal Lab** record by hand or through a TB-LIS import.
5. A clinician records the **Diagnosis**, and any **Regimen Changes** after that.
6. Reviewers and admins track progress through Form Status, Dashboard and Reports, resolve
   data-quality queries, and export data.
