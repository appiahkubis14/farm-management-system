# App API Structure & Modules Report

This document lists the API structure for all features in the app, including existing endpoints and data structures (JSON payloads) to be sent to the backend.

## 1. Authentication & User
**Module Description:** Handles user login and profile management.

**API Structure:**
- **Endpoint:** `/api/v1/auth/login/`
- **Method:** `POST`
- **Payload:**
  ```json
  {
    "username": "user_input",
    "password": "user_input"
  }
  ```

---

## 2. Daily Reporting
**Module Description:** Captures daily farm activities (weeding, planting, etc.) and labor usage.

**API Structure:**
- **Endpoint:** `/api/v1/saveactivityreport/`
- **Method:** `POST`
- **Payload (DailyReportingModel):**
  ```json
  {
    "uid": "uuid-v4-string",
    "agent": "user_id",
    "completion_date": "YYYY-MM-DD",
    "reporting_date": "YYYY-MM-DD",
    "main_activity": "activity_code",
    "activity": "sub_activity_code",
    "no_rehab_assistants": 5,
    "area_covered_ha": 1.5,
    "remark": "Optional comments",
    "status": 0, // 0=Pending, 1=Submitted
    "farm_ref_number": "farm_id",
    "farm_size_ha": 2.0,
    "community": "community_id",
    "number_of_people_in_group": 10,
    "group_work": "Yes/No",
    "sector": "sector_id",
    "ras": "list_of_ra_ids"
  }
  ```

---

## 3. Activity Reporting (Initial Treatment Monitoring)
**Module Description:** Monitors initial treatment activities on outbreak farms.

**API Structure:**
- **Endpoint:** `/api/v1/saveactivityreport/`
- **Note:** Code uses the same endpoint as Daily Reporting. The `saveMonitoring` endpoint (`/api/v1/savemonitoringform/`) appears unused.
- **Method:** `POST`
- **Payload (InitialTreatmentMonitorModel):**
  ```json
  {
    "uid": "uuid-v4-string",
    "agent": "user_id",
    "main_activity": "activity_code",
    "activity": "sub_activity_code",
    "completed_date": "YYYY-MM-DD",
    "reporting_date": "YYYY-MM-DD",
    "no_rehab_assistants": 3,
    "area_covered_ha": 1.2,
    "remark": "Field notes",
    "ras": "list_of_ra_ids",
    "submission_status": 0,
    "farm_ref_number": "farm_id",
    "farm_size_ha": 5.0,
    "community": "community_id",
    "number_of_people_in_group": 10,
    "groupWork": "Yes/No",
    "sector": 1
  }
  ```

---

## 4. Add Personnel
**Module Description:** Registers new personnel (Rehab Assistants, etc.) into the system.

**API Structure:**
- **Endpoint:** `/api/v1/saveregister/`
- **Method:** `POST`
- **Payload (CmUser/PersonnelModel):**
  ```json
  {
    "first_name": "John",
    "surname": "Doe",
    "other_names": "Kwame",
    "gender": "Male",
    "date_of_birth": "YYYY-MM-DD",
    "primary_phone_number": "024XXXXXXX",
    "secondary_phone_number": "050XXXXXXX",
    "momo_number": "024XXXXXXX",
    "emergency_contact_person": "Jane Doe",
    "emergency_contact_number": "020XXXXXXX",
    "id_type": "Voter ID",
    "id_number": "123456789",
    "address": "123 Street, City",
    "community": "CommunityName",
    "district": "DistrictID",
    "education_level": "Tertiary",
    "marital_status": "Single",
    "bank_id": "BankID",
    "account_number": "1234567890",
    "branch_id": "BranchID",
    "sort_code": "SortCode",
    "personnel_type": "Rehab Assistant",
    "ezwich_number": "123456",
    "date_joined": "YYYY-MM-DD",
    "supervisor_id": "SupervisorID",
    "image": "base64_string",
    "id_image_front": "base64_string",
    "id_image_back": "base64_string",
    "consent_form_image": "base64_string"
  }
  ```

---

## 5. Assign Rehab Assistant (RA)
**Module Description:** Assigns a Rehab Assistant to a specific community or task.

**API Structure:**
- **Endpoint:** `/api/v1/saverehabasssignment/`
- **Method:** `POST`
- **Payload (PersonnelAssignmentModel):**
  ```json
  {
    "uid": "uuid-v4-string",
    "po_id": "project_officer_id",
    "ra_id": "rehab_assistant_id",
    "district_id": "district_id",
    "community_id": "community_id",
    "date_assigned": "YYYY-MM-DD",
    "status": 0 // 0=Pending, 1=Submitted
  }
  ```

---

## 6. Growth Monitoring
**Module Description:** Tracks the growth metrics of crops over time.

**API Structure:**
- **Endpoint:** `/api/v1/growth_monitoring`
- **Method:** `POST`
- **Payload (GrowthMonitoringModel):**
  ```json
  {
    "uid": "uuid-v4-string",
    "plant_uid": "plant_id",
    "number_of_leaves": 15,
    "height": 120.5,
    "stem_size": 2.5,
    "leaf_color": "Green",
    "date": "YYYY-MM-DD",
    "lat": 5.6037,
    "lng": -0.1870,
    "agent": "user_id"
  }
  ```

---

## 7. Outbreak Farm
**Module Description:** Records details of farms affected by outbreaks (e.g., swollen shoot).

**API Structure:**
- **Endpoint:** `/api/v1/saveoutbreakfarm/`
- **Method:** `POST`
- **Payload (OutbreakFarmModel):**
  ```json
  {
    "uid": "uuid-v4-string",
    "farmer_name": "Farmer Name",
    "farm_location": "Location",
    "community": "CommunityID",
    "farm_size": 5.0,
    "disease_type": "DiseaseID",
    "date_reported": "YYYY-MM-DD",
    "reported_by": "user_id",
    "status": 0, // 0=Pending, 1=Submitted
    "coordinates": "lat,lng"
  }
  ```

---

## 8. Contractor Certificate
**Module Description:** Manages contractor work certificates and verifications.

**API Structure (Certificate):**
- **Endpoint:** `/api/v1/saveContractorcertificateofworkdone/`
- **Method:** `POST`
- **Payload (ContractorCertificateModel):**
  ```json
  {
    "uid": "uuid-v4-string",
    "contractor_id": "contractor_id",
    "work_type": "work_type_id",
    "start_date": "YYYY-MM-DD",
    "end_date": "YYYY-MM-DD",
    "status": "Pending/Approved",
    "remarks": "comments"
  }
  ```

**API Structure (Verification):**
- **Endpoint:** `/api/v1/saveverificationfarms/`
- **Method:** `POST`
- **Payload (ContractorCertificateVerificationModel):**
  ```json
  {
    "uid": "uuid-v4-string",
    "certificate_id": "certificate_uid",
    "verified_by": "user_id",
    "verification_date": "YYYY-MM-DD",
    "is_verified": true,
    "comments": "verification notes"
  }
  ```

---

## 9. Submit Issue / Feedback
**Module Description:** Allows users to submit issues or feedback.

**API Structure:**
- **Endpoint:** `/api/v1/savefeedback/`
- **Method:** `POST`
- **Payload (IssueModel):**
  ```json
  {
    "uid": "uuid-v4-string",
    "user_id": "user_id",
    "issue_type": "type_id",
    "description": "Issue description text",
    "date_reported": "YYYY-MM-DD",
    "status": 0 // 0=Pending, 1=Submitted
  }
  ```

---

## 10. Irrigation
**Module Description:** Tracks irrigation activities.

**API Structure:**
- **Status:** No existing endpoint found in `constants.dart` or `IrrigationDao`.
- **Recommendation:** Needs a new endpoint if backend sync is required.
- **Proposed Endpoint (Placeholder):** `/api/v1/saveirrigation/`
- **Payload Structure (Based on Local DB):**
  ```json
  {
    "uid": "uuid-v4-string",
    "farm_id": "farm_id",
    "irrigation_type": "drip/sprinkler",
    "water_volume": 100.0,
    "date": "YYYY-MM-DD",
    "agent": "user_id"
  }
  ```

---

## 11. General Data Loading
**Module Description:** Endpoints for fetching dropdown data and configurations.

- **Load Regions/Districts:** `/api/v1/regiondistricts/`
- **Load Contractors:** `/api/v1/fetchallcontractors/`
- **Load Activities:** `/api/v1/activity/`
- **Load Farms:** `/api/v1/farms/`
- **Load Communities:** `/api/v1/fetchcommunity/`
- **Load Job Order Farms:** `/api/v1/fetchjoborder/`
- **Load Rehab Assistants:** `/api/v1/fetchrehabassistants/`

---

## 12. Payment Report
**Module Description:** Generates summary payment reports for personnel.

**API Structure:**
- **Endpoint:** `/api/v1/fetchpayments/`
- **Method:** `POST`
- **Payload:**
  ```json
  {
    "userid": "user_id",
    "month": "MonthName",
    "week": "WeekNumber",
    "year": "YYYY"
  }
  ```
- **Response Data (Report):**
  ```json
  [
    {
      "ra_id": "RA ID",
      "ra_name": "Name",
      "district": "District",
      "bank_name": "Bank",
      "bank_branch": "Branch",
      "snnit_no": "SNNIT",
      "salary": "Amount",
      "year": "YYYY",
      "po_number": "PO#",
      "month": "Month",
      "week": "Week",
      "payment_option": "Momo/Bank",
      "momo_acc": "Momo Number"
    }
  ]
  ```

---

## 13. Detailed Payment Report
**Module Description:** Generates detailed breakdown of payments and activities.

**API Structure:**
- **Endpoint:** `/api/v1/fetchpaymentdetailedreport/`
- **Method:** `POST`
- **Payload:**
  ```json
  {
    "userid": "user_id",
    "month": "MonthName",
    "week": "WeekNumber",
    "year": "YYYY"
  }
  ```
- **Response Data (DetailedReport):**
  ```json
  [
    {
      "group_code": "Code",
      "ra_id": "RA ID",
      "ra_name": "Name",
      "po_name": "PO Name",
      "po_number": "PO#",
      "district": "District",
      "farmhands_type": "Type",
      "farm_reference": "Ref",
      "number_in_a_group": "Count",
      "activity": "Activity Name",
      "achievement": 10.5,
      "amount": "100.00",
      "week": "Week",
      "month": "Month",
      "year": "YYYY",
      "issue": "Issues if any"
    }
  ]
  ```

---

## 14. Assigned Blocks (Farms & Outbreaks)
**Module Description:** Fetches assigned farms and outbreak areas for map visualization.

**API Structure (Assigned Farms):**
- **Endpoint:** `/api/v1/fetchpoassignedfarms/`
- **Method:** `GET` (Inferred)
- **Payload:**
  ```json
  {
    "user_id": "user_id" // Likely required
  }
  ```
- **Response Data (AssignedFarm):**
  ```json
  [
    {
      "id": 1,
      "farm_boundary": "utf8_encoded_string_or_blob",
      "farmername": "Farmer Name",
      "location": "Location Name",
      "farm_reference": "Ref Code",
      "farm_size": "Size in Ha"
    }
  ]
  ```

**API Structure (Assigned Outbreaks):**
- **Endpoint:** `/api/v1/fetchoutbreak/`
- **Method:** `POST` (Inferred)
- **Response Data (AssignedOutbreak):**
  ```json
  [
    {
      "ob_id": 1,
      "ob_code": "Outbreak Code",
      "ob_size": "Size in Ha",
      "district_id": 101,
      "district_name": "District Name",
      "region_id": "Region ID",
      "region_name": "Region Name",
      "ob_boundary": "utf8_encoded_string_or_blob"
    }
  ]
  ```

---

## 15. Verification (Video Record)
**Module Description:** Records video verification for farm job orders.

**API Structure:**
- **Endpoint:** `/api/v1/saveverificationrecord/`
- **Method:** `POST`
- **Payload:** `FormData`
  - `uid`: UUID String
  - `farmRef`: Farm Reference Number
  - `timestamp`: ISO-8601 Date String
  - `status`: Integer (0=Pending, 1=Synced)
  - `video`: MultipartFile (Video file)

**Local Data Structure (VerifyRecord):**
```json
{
  "uid": "uuid-v4-string",
  "farmRef": "Farm Reference Number",
  "videoPath": "/path/to/local/video.mp4",
  "timestamp": "ISO-8601 Date String",
  "status": 0 // 0=Pending, 1=Synced
}
```

---

## 16. Area Calculation
**Module Description:** Polygon drawing tool for calculating farm areas.

**API Structure:**
- **Endpoint:** `/api/v1/savecalculatedarea/`
- **Method:** `POST`
- **Payload:**
  ```json
  {
    "date": "ISO-8601 Date String",
    "title": "Area Title/Name",
    "value": "10.5" // Area in Hectares
  }
  ```

**Local Data Structure (CalculatedArea):**
```json
{
  "id": 1,
  "date": "ISO-8601 Date String",
  "title": "Area Title/Name",
  "value": "10.5" // Area in Hectares
}
```
