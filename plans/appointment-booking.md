# Implementation Plan - Appointment Booking System

This plan outlines the steps to implement a complete Appointment Booking system within the Uprising Prospect CRM, including backend models, API endpoints, and a frontend calendar interface.

## 1. Backend Development

### 1.1. Data Models
- **File**: `src/core/models.py`
  - Add `AppointmentStatus` Enum: `scheduled`, `completed`, `cancelled`, `no-show`.
  - Add `Appointment` Pydantic model: `id`, `lead_id`, `title`, `description`, `start_at`, `end_at`, `status`, `location`, `meeting_link`, `opportunity_id`, `created_at`, `updated_at`.
- **File**: `src/core/db_models.py`
  - Add `DBAppointment` SQLAlchemy model with appropriate relationships and indexes.

### 1.2. API Endpoints
- **File**: `src/api/server.py`
  - `GET /api/v1/admin/appointments`: List all appointments.
  - `GET /api/v1/admin/leads/{lead_id}/appointments`: List appointments for a specific lead.
  - `POST /api/v1/admin/appointments`: Create a new appointment.
  - `PATCH /api/v1/admin/appointments/{id}`: Update appointment (status, time, etc.).
  - `DELETE /api/v1/admin/appointments/{id}`: Cancel/Delete appointment.

## 2. Frontend Development

### 2.1. Internationalization (i18n)
- **Files**: `admin-dashboard/lib/i18n/types.ts`, `fr.ts`, `en.ts`
  - Add translations for "Appointments", "Book Appointment", "Calendar", etc.

### 2.2. UI Components
- **New Component**: `admin-dashboard/components/ui/calendar.tsx` (Simple calendar or use `react-day-picker` patterns).
- **New Component**: `admin-dashboard/components/book-appointment-modal.tsx`: Form to schedule a meeting with a lead.
- **New Component**: `admin-dashboard/components/appointments-calendar.tsx`: Full-page calendar view.

### 2.3. Navigation & Pages
- **File**: `admin-dashboard/components/app-sidebar.tsx`: Add "Appointments" link to the sidebar.
- **New Page**: `admin-dashboard/app/appointments/page.tsx`: Main calendar view for all appointments.
- **File**: `admin-dashboard/app/leads/[id]/page.tsx`:
  - Add "Appointments" tab to the lead detail view.
  - List upcoming appointments for the lead.
  - Add button to open `BookAppointmentModal`.

## 3. Verification Plan

### 3.1. Backend Tests
- Create a new test file `tests/test_admin_appointments_api.py`.
- Test CRUD operations for appointments.
- Verify relationship with leads.

### 3.2. Frontend Verification
- Manually verify the new sidebar link.
- Test booking an appointment from the Lead detail page.
- Verify the appointment appears on the main Calendar page.
- Test updating/cancelling an appointment.
