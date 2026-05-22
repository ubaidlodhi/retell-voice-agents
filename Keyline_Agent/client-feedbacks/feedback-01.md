**Aubrey Voice Agent - Updates & Monday.com Enhancements**

**Aubrey (Retell AI) Changes**

- Remove the email address collection step from Aubrey's call flow (causing slowdowns and errors)
- Slightly increase Aubrey's response speed without cutting off callers
- Update caller data collection logic:
    - If caller is a caregiver: collect patient name
    - If caller is a patient: collect family caregiver's name
    - If caller is a case manager: collect client name and family caregiver's name (if available)
    
**Monday.com Changes**
    
- Set up automatic email notification to Gloria@Keylinehomecare.com for all calls related to incident reports
- Add a Patient Name column to the case support boards
- Add an automatic recording link column on the case support boards (to allow direct playback from Monday.com without going to Retell)
- Recreate the following automations:
    - Notify team when a new ticket is created
    - Notify team if a ticket remains in NEW status after 2 days
    - Notify team if a ticket remains in IN REVIEW status after 2 days