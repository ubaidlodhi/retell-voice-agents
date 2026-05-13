# CreateBooking

# Package: bookings

# Namespace: Bookings

# Method link: https://dev.wix.com/docs/api-reference/business-solutions/bookings/bookings/bookings-writer-v2/create-booking.md

## Permission Scopes:
Manage Bookings: SCOPE.DC-BOOKINGS.MANAGE-BOOKINGS

## Introduction

Creates a booking.

---

## REST API

### Schema

```
 Method: createBooking
 Description: Creates a booking.   ### Appointment booking  For appointment-based services, specify the relevant time slot in `bookedEntity.slot`.  We recommend following the [appointment booking sample flow](https://dev.wix.com/docs/api-reference/business-solutions/bookings/bookings/bookings-writer-v2/sample-flows.md#book-an-appointment) using Time Slots V2. Specify the slot's `startDate`, `endDate`, `resource`, and `location` in `booking.bookedEntity.slot`.  ### Class session booking  For class services, specify the relevant event GUID as `bookedEntity.slot.eventId`.  We recommend following the [class session booking sample flow](https://dev.wix.com/docs/api-reference/business-solutions/bookings/bookings/bookings-writer-v2/sample-flows.md#book-a-class-session) using Time Slots V2. Specify the `eventId` from the selected time slot in `booking.bookedEntity.slot.eventId`.  When you specify `eventId`, Wix Bookings automatically derives `startDate`, `endDate`, `timezone`, `resource`, and `location` based on the event details. Manually specified values are ignored.  ### Course booking  For course services, specify the course's schedule GUID in `bookedEntity.schedule.scheduleId`. We recommend following [this sample flow](https://dev.wix.com/docs/rest/business-solutions/bookings/end-to-end-booking-flows.md#book-a-course) to minimize failed calls due to unavailability.  ### Booking status  Create Booking defaults to `status=CREATED`. Such bookings aren't visible in the [Booking Calendar](https://support.wix.com/en/article/wix-bookings-about-the-wix-booking-calendar).  Only [identities](https://dev.wix.com/docs/build-apps/develop-your-app/access/about-identities.md) with `Manage Bookings` permissions can set `status=CONFIRMED`.  ### Related resources  Specifying a `resource` triggers an availability check, and the Create Booking call fails if the resource is unavailable.  If you omit `resource`, resource assignment and availability validation occur during booking confirmation. If no resources are available, the behavior depends on the confirmation method used and payment status.  ### Booking form data  When customers sign up for a service, they must fill out the [booking form](https://support.wix.com/en/article/wix-bookings-creating-and-setting-up-your-booking-forms). To create a booking with a completed booking form, specify the relevant data in `formSubmission`. When specifying `formSubmission`, Wix Bookings sets all `booking.contactDetails` fields based on `formSubmission` and ignores any values in `booking.contactDetails`, except for `booking.contactDetails.contactId`. To avoid conflicts, send `booking.contactDetails.contactId` together with `formSubmission`, and omit other contact details. Learn more about the [Bookings and Wix Forms integration](https://dev.wix.com/docs/rest/business-solutions/bookings/wix-forms-integration.md).  ### Participant information  You must specify either `participantsChoices` or `totalParticipants`. The call fails if the specified `participantsChoices` aren't among the supported [service options and variants](https://dev.wix.com/docs/rest/business-solutions/bookings/services/service-options-and-variants/introduction.md).  ### Add-ons  You can include [add-ons](https://dev.wix.com/docs/api-reference/business-solutions/bookings/services/add-ons/introduction.md) when creating a booking by specifying `bookedAddOns`. Each selected add-on must belong to an [add-on group](https://dev.wix.com/docs/api-reference/business-solutions/bookings/services/services-v2/about-add-on-groups.md) associated with the service and respect the group's selection limits.  ### Notify customers  You can specify a `participantNotification.message` for the customer that's send immediately. Ensure `participantNotification.notifyParticipants` is set to `true` to send the message.  If you specify `{"sendSmsReminder": true}`, the customer receives an SMS 24 hours before the session starts. The phone number is taken from `contactDetails.phone`.  ### Payment options  The specified `selectedPaymentOption` indicates how the customer intends to pay, allowing for later changes to a different method supported by the service.  When the customer pays with a [Wix eCommerce checkout](https://dev.wix.com/docs/api-reference/business-solutions/e-commerce/purchase-flow/checkout/introduction.md), you must specify a `selectedPaymentOption`. Otherwise, the Create Booking call fails. For custom checkouts, you don't have to specify a `selectedPaymentOption`.  ### Payment status  All bookings are created with `paymentStatus=UNDEFINED`, ignoring the payment status you specify.  For customers paying with a [Wix eCommerce checkout](https://dev.wix.com/docs/rest/business-solutions/e-commerce/purchase-flow/checkout/checkout/introduction.md), Wix Bookings automatically syncs the booking's payment status from the corresponding [eCommerce order](https://dev.wix.com/docs/rest/business-solutions/e-commerce/orders/introduction.md).  For customers using a custom checkout, call [Confirm or Decline Booking](https://dev.wix.com/docs/rest/business-solutions/bookings/bookings/bookings-writer-v2/confirm-or-decline-booking.md) to update booking's payment status manually.  ### Admin overwrites  There are small but important differences when you specify special `flowControlSettings`:  - `{"skipAvailabilityValidation": true}`: The call succeeds regardless of availability. If you don't specify any resource, the call succeeds even if no resource of the relevant type is available. - `{"skipBusinessConfirmation": true}`: Automatically confirms `PENDING` bookings that require manual confirmation. - `{"skipSelectedPaymentOptionValidation": true}`: Allows customers to pay with payment methods that aren't supported for the service. - `{"skipAddOnValidation": true}`: Allows customers to choose add-ons that aren't associated with the service or exceed group selection limits. - `{"allowAddOnChanges": true}`: Allows customers to update the list of add-ons associated with the booking when rescheduling.  When using special `flowControlSettings`, ensure you have sufficient permissions. If you encounter failed calls due to insufficient permissions, consider the following options:  - **App developers** can use a higher [permission](https://dev.wix.com/docs/build-apps/develop-your-app/access/authorization/about-permissions.md), such as `MANAGE BOOKINGS - ALL PERMISSIONS`. - **Site developers** can utilize [elevation](https://dev.wix.com/docs/develop-websites/articles/coding-with-velo/authorization/elevation.md).  Granting additional permissions and using elevation permits method calls that would typically fail due to authorization checks. Therefore, you should use them intentionally and securely.
 URL: https://www.wixapis.com/_api/bookings-service/v2/bookings
 Method: POST
 Required parameters: booking, booking.bookedEntity, booking.additionalFields.id
 Method parameters: 
   param name: booking | type: Booking | description: An entity representing a scheduled appointment, class session, or course. | required: true
    - ONE-OF: - required: true
     - name: totalParticipants | type: integer | description: Total number of participants. When creating a booking, use this field only if the relevant service has fixed pricing and doesn't offer [variants and options](https://dev.wix.com/docs/rest/business-solutions/bookings/services/service-options-and-variants/introduction.md). 
     - name: participantsChoices | type: ParticipantChoices | description: Information about the booked service choices and participant count for each choice. When creating a booking, use this field only if the booking includes multiple [service variants](https://dev.wix.com/docs/rest/business-solutions/bookings/services/service-options-and-variants/introduction.md).  For example, use this for a spa package booking that includes different service levels: - 2 participants chose "Standard Package". - 1 participant chose "VIP Package". 
        - name: serviceChoices | type: array<ServiceChoices> | description: Information about the booked service choices. Includes the number of participants. 
           - name: numberOfParticipants | type: integer | description: Number of participants for this [variant](https://dev.wix.com/docs/rest/business-solutions/bookings/services/service-options-and-variants/introduction.md). 
           - name: choices | type: array<ServiceChoice> | description: Service choices for these participants. 
              - ONE-OF: 
                 - name: custom | type: string | description: Value for one of the choices in the [`CustomServiceOption.choices`](https://example.com) list. Choices are specific values for an option the customer can choose to book. For example, the option `ageGroup` may have these choices: `child`, `student`, `adult`, and `senior`. Each choice may have a different price. 
                 - name: duration | type: Duration | description:  
                    - name: minutes | type: integer | description: Duration of the service in minutes. Min: 1 minute, Max: 30 days, 23 hours, and 59 minutes 
                    - name: name | type: string | description: Name of the duration option. Defaults to the formatted duration e.g. "1 hour, 30 minutes". 
              - name: optionId | type: string | description: GUID of the corresponding option for the choice. For example, the choice `child` could correspond to the option `ageGroup`. In this case, `optionId` is the GUID for the `ageGroup` option. 
        - name: bookedEntity | type: BookedEntity | description: An object describing the bookable entity - either a specific time slot or a recurring schedule.  The structure depends on the type of service being booked:  __For appointment services__: Use `slot` to book a specific time slot with a service provider. Appointments are typically one-time sessions at a specific date and time.  __For class services__: Use `slot` to book a specific class session. Classes are individual sessions that can have multiple participants.  __For course services__: Use `schedule` to book an entire course consisting of multiple sessions over time. Courses are recurring, multi-session offerings.  Choose the appropriate field based on your service type and booking requirements. | required: true
           - ONE-OF: 
              - name: slot | type: BookedSlot | description: [Booked slot](https://dev.wix.com/docs/rest/business-solutions/bookings/bookings-and-time-slots/time-slots/availability-calendar/query-availability.md).  Specify `slot` when creating bookings for: - __Appointment-based services__: Individual sessions with service providers (consultations, treatments). Wix Bookings creates a new session when the booking is confirmed. - __Class services__: Group sessions at specific times (fitness classes, workshops). Wix Bookings links the booking to an existing scheduled session.  For course services, specify `schedule` instead of `slot`. 
                 - name: serviceId | type: string | description: Service GUID. 
                 - name: scheduleId | type: string | description: Schedule GUID. 
                 - name: eventId | type: string | description: GUID of the corresponding [event](https://dev.wix.com/docs/rest/business-management/calendar/events-v3/introduction.md). Available for both appointment and class bookings, not available for course bookings. For appointment-based services, Wix Bookings automatically populates `eventId` when the booking `status` changes to `CONFIRMED`. For class bookings, Wix Bookings automatically populates `eventId` upon booking creation. 
                 - name: startDate | type: string | description: The start time of this slot in `YYYY-MM-DDThh:mm:ss`, `YYYY-MM-DDThh:mm:ss:SSS`, or `YYYY-MM-DDThh:mm:ss:SSSZZ` [ISO-8601 format](https://en.wikipedia.org/wiki/ISO_8601). For example, `2026-01-30T13:30:00`, `2026-01-30T13:30:00:000`, or `2026-01-30T13:30:00:000-05:00`. 
                 - name: endDate | type: string | description: The end time of this slot in `YYYY-MM-DDThh:mm:ss`, `YYYY-MM-DDThh:mm:ss:SSS`, or `YYYY-MM-DDThh:mm:ss:SSSZZ` [ISO-8601 format](https://en.wikipedia.org/wiki/ISO_8601). For example, `2026-01-30T13:30:00`, `2026-01-30T13:30:00:000`, or `2026-01-30T13:30:00:000-05:00`. 
                 - name: timezone | type: string | description: Time zone in [IANA tz database format](https://en.wikipedia.org/wiki/Tz_database). For example, `America/New_York` or `UTC`. This is the time zone in which the slot was shown to the customer at the time of booking. Wix Bookings ensures that the slot is always displayed in this same time zone to the customer, including when they view or edit their booking in the future. 
                 - name: resource | type: BookedResource | description: [Primary resource](https://dev.wix.com/docs/rest/business-solutions/bookings/resources/resources-v2/introduction.md) for the booking. For example, the [staff member](https://dev.wix.com/docs/rest/business-solutions/bookings/staff-members/introduction.md) providing the service. 
                    - name: id | type: string | description: GUID of the booking's primary resource. 
                    - name: name | type: string | description: Resource's name at the time of booking. 
                    - name: email | type: string | description: Resource's email at the time of booking. 
                    - name: scheduleId | type: string | description: GUID of the schedule belonging to the booking's primary resource. 
                 - name: location | type: Location | description: Location where the session takes place. 
                    - name: id | type: string | description: Business location GUID. Available only for locations that are business locations, meaning the `location_type` is `"OWNER_BUSINESS"`. 
                    - name: name | type: string | description: Location name. 
                    - name: formattedAddress | type: string | description: The full address of this location. 
                    - name: formattedAddressTranslated | type: string | description: The full translated address of this location. 
                    - name: locationType | type: LocationType | description: Location type. 
                             - enum:
                             -     UNDEFINED: Undefined location type.
                             -     OWNER_BUSINESS: The business address, as set in the site’s general settings.
                             -     OWNER_CUSTOM: The address as set when creating the service.
                             -     CUSTOM: The address as set for the individual session.
                 - name: resourceSelections | type: array<ResourceSelection> | description: Information about how the customer has selected resources for the booking. Each resource type may have a different selection method. Check `resource` for resource details. 
                    - name: resourceTypeId | type: string | description: GUID of the [resource type](https://dev.wix.com/docs/api-reference/business-solutions/bookings/resources/resource-types-v2/introduction.md). 
                    - name: selectionMethod | type: SelectionMethod | description: Information about how the customer has selected the resource for this resource type. 
                             - enum:
                             -     SPECIFIC_RESOURCE: The customer explicitly chose a particular resource.
                             -     ANY_RESOURCE: The customer explicitly chose "any available resource" for this resource type.
                             -     NO_SELECTION: The customer wasn't offered a resource selection or agreement option for this resource type.
              - name: schedule | type: BookedSchedule | description: [Booked schedule](https://dev.wix.com/docs/rest/business-management/calendar/schedules-v3/introduction.md).  Specify `schedule` when creating bookings for: - __Course services__: Multi-session offerings spanning weeks or months (educational courses, training programs). Wix Bookings enrolls participants in all sessions defined by the course schedule. 
                 - name: scheduleId | type: string | description: [Schedule GUID](https://dev.wix.com/docs/rest/business-management/calendar/schedules-v3/introduction.md). 
                 - name: serviceId | type: string | description: Booked service GUID. 
                 - name: timezone | type: string | description: Time zone in [IANA tz database format](https://en.wikipedia.org/wiki/Tz_database). For example, `America/New_York` or `UTC`. This is the time zone in which the schedule was shown to the customer at the time of booking. Wix Bookings ensures that the schedule is always displayed in this same time zone to the customer, including when they view or edit their booking in the future. 
           - name: tags | type: array | description: List of tags for the booking.  - "INDIVIDUAL": For bookings of appointment-based services. Including when the appointment is for a group of participants. - "GROUP": For bookings of individual class sessions. - "COURSE": For course bookings. 
        - name: contactDetails | type: ContactDetails | description: Contact details of the site visitor or [member](https://dev.wix.com/docs/api-reference/crm/members-contacts/members/members/introduction.md) making the booking. 
           - name: contactId | type: string | description: Contact GUID. 
           - name: firstName | type: string | description: Contact's first name. When populated from a standard booking form, this property corresponds to the `name` field. 
           - name: lastName | type: string | description: Contact's last name. 
           - name: email | type: string | description: Contact's email. If no [contact](https://dev.wix.com/docs/rest/crm/members-contacts/contacts/contacts/contact-v4/contact-object.md) with this email exist, a new contact is created. Used to validate coupon usage limitations per contact. If not specified, the coupon usage limitation will not be enforced. (Coupon usage limitation validation is not supported yet). 
           - name: phone | type: string | description: Contact's phone number. 
           - name: fullAddress | type: Address | description: Contact's full address. 
              - ONE-OF: 
                 - name: streetAddress | type: StreetAddress | description: Street name, number and apartment number. 
                    - name: number | type: string | description: Street number. 
                    - name: name | type: string | description: Street name. 
                    - name: apt | type: string | description: Apartment number. 
                 - name: addressLine | type: string | description: Main address line, usually street and number, as free text. 
              - name: country | type: string | description: Country code. 
              - name: subdivision | type: string | description: Subdivision. Usually state, region, prefecture or province code, according to [ISO 3166-2](https://en.wikipedia.org/wiki/ISO_3166-2). 
              - name: city | type: string | description: City name. 
              - name: postalCode | type: string | description: Zip/postal code. 
              - name: addressLine2 | type: string | description: Free text providing more detailed address info. Usually contains Apt, Suite, and Floor. 
              - name: formattedAddress | type: string | description: A string containing the full address of this location. 
              - name: hint | type: string | description: Free text to help find the address. 
              - name: geocode | type: AddressLocation | description: Coordinates of the physical address. 
                 - name: latitude | type: number | description: Address latitude. 
                 - name: longitude | type: number | description: Address longitude. 
              - name: countryFullname | type: string | description: Country full name. 
              - name: subdivisions | type: array<Subdivision> | description: Multi-level subdivisions from top to bottom. 
                 - name: code | type: string | description: Subdivision code. Usually state, region, prefecture or province code, according to [ISO 3166-2](https://en.wikipedia.org/wiki/ISO_3166-2). 
                 - name: name | type: string | description: Subdivision full name. 
           - name: countryCode | type: string | description: Contact's country in [ISO 3166-1 alpha-2 code](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) format. 
        - name: status | type: BookingStatus | description: Booking status. A booking is automatically confirmed if the service allows it and an eCommerce order is created. It is automatically declined if there is a double booking and the customer hasn't paid or is eligible for an automatic refund. Currently, only payments with pricing plans are automatically refundable. 
             - enum:
             -     CREATED: The booking was created, but the customer hasn't completed the related eCommerce order yet.
             -     CONFIRMED: The merchant has confirmed the booking and it appears in the business calendar. Merchants can set up their [services](https://dev.wix.com/docs/rest/business-solutions/bookings/services/services-v2/introduction.md) to automatically confirm all `PENDING` bookings.
             -     CANCELED: The customer has canceled the booking. Depending on the relevant service's [policy snapshot](https://dev.wix.com/docs/rest/business-solutions/bookings/policies/booking-policy-snapshots/introduction.md) they may have to pay a [cancellation fee](https://dev.wix.com/docs/rest/business-solutions/bookings/pricing/booking-fees/introduction.md).
             -     PENDING: The merchant must manually confirm the booking before it appears in the business calendar.
             -     DECLINED: The merchant has declined the booking before the customer was charged.
             -     WAITING_LIST: Currently, you can't call [Register to Waitlist](https://dev.wix.com/docs/rest/business-solutions/bookings/bookings/waitlist/register-to-waitlist.md) for course or appointment bookings, even though this is supported in live sites.
        - name: paymentStatus | type: PaymentStatus | description: The payment status of the booking. This field automatically syncs with the `paymentStatus` of the corresponding [eCommerce order](https://dev.wix.com/docs/api-reference/business-solutions/e-commerce/orders/introduction.md) when customers use Wix eCommerce checkout.  ### Integration patterns  __When using Wix eCommerce checkout__: Wix Bookings automatically syncs the payment status based on the eCommerce order's payment status. Do not manually update this field.  __When using custom payment flows__: You can manually update the payment status with [Confirm Booking or Decline Booking](https://dev.wix.com/docs/api-reference/business-solutions/bookings/bookings/bookings-writer-v2/confirm-or-decline-booking.md) to reflect the customer's payment state.  __For membership/pricing plan payments__: Wix Bookings automatically manages the payment status when customers pay with an active [pricing plan](https://dev.wix.com/docs/api-reference/business-solutions/pricing-plans/pricing-plans/introduction.md) subscription.  All payment statuses are supported for every booking `status`. 
             - enum:
             -     UNDEFINED: Undefined payment status.
             -     NOT_PAID: The booking isn't paid.
             -     PAID: The booking is fully paid.
             -     PARTIALLY_PAID: The booking is partially paid.
             -     REFUNDED: The booking is refunded.
             -     EXEMPT: The booking is free of charge.
        - name: selectedPaymentOption | type: SelectedPaymentOption | description: Payment option selected by the customer. If the customer hasn't completed their checkout, they may still change the payment method. Must be one of the payment options offered by the [service](https://dev.wix.com/docs/api-reference/business-solutions/bookings/services/services-v2/introduction.md), unless `skipSelectedPaymentOptionValidation` is `true`.  When the customer pays with a [Wix eCommerce checkout](https://dev.wix.com/docs/api-reference/business-solutions/e-commerce/checkout/introduction.md), this field is required. Otherwise, the Create Booking call fails. For custom checkouts, you don't have to specify this field. 
             - enum:
             -     UNDEFINED: Undefined payment option.
             -     OFFLINE: Offline payment.
             -     ONLINE: Online payment.
             -     MEMBERSHIP: Payment using a Wix Pricing Plan.
             -     MEMBERSHIP_OFFLINE: Customers can pay only in person with a Wix Pricing Plan, while the Wix user must manually redeem the pricing plan in the dashboard.
        - name: externalUserId | type: string | description: External user GUID that you can provide. 
        - name: revision | type: string | description: Revision number to be used when updating, rescheduling, or cancelling the booking. Increments by 1 each time the booking is updated, rescheduled, or canceled. To prevent conflicting changes, the current revision must be specified when updating the booking. 
        - name: extendedFields | type: ExtendedFields | description: Custom field data for this object. Extended fields must be configured in the app dashboard before they can be accessed with API calls. 
           - name: namespaces | type: object | description: Extended field data. Each key corresponds to the namespace of the app that created the extended fields. The value of each key is structured according to the schema defined when the extended fields were configured.  You can only access fields for which you have the appropriate permissions.  Learn more about [extended fields](https://dev.wix.com/docs/rest/articles/getting-started/extended-fields.md). 
        - name: formSubmissionId | type: string | description: GUID of the [form submission](https://dev.wix.com/docs/rest/crm/forms/form-submissions/introduction.md) associated with this booking. 
        - name: bookedAddOns | type: array<BookedAddOn> | description: List of [add-ons](https://dev.wix.com/docs/api-reference/business-solutions/bookings/services/add-ons/introduction.md) associated with the booking. 
           - name: id | type: string | description: The GUID of the add-on. 
           - name: groupId | type: string | description: The GUID of the add-on group. 
           - name: quantity | type: integer | description: The quantity of booked add-ons. For duration-based add-ons, `quantity` is not applicable. If `quantity` is provided as `1` for a duration-based add-on, it will be accepted but the value will be cleared. If any other value is provided, an `INVALID_ARGUMENT` error will be returned with the message: "Invalid AddOn details: either duration or quantity must be set correctly". 
        - name: depositSelected | type: boolean | description: Whether the customer chooses to pay only the deposit amount upfront.  - `true`: The customer pays only the deposit amount upfront. - `false`: The customer pays the full price upfront.  Used only when `selectedPaymentOption` is `ONLINE` and the [service](https://dev.wix.com/docs/api-reference/business-solutions/bookings/services/services-v2/introduction.md) has a deposit amount set.  When the service supports deposit payments and `fullUpfrontPaymentAllowed` is `false`, this field must be `true`. When the service supports deposit payments and `fullUpfrontPaymentAllowed` is `true`, this field can be `true` or `false`. 
   param name: flowControlSettings | type: CreateBookingFlowControlSettings   
        - name: skipAvailabilityValidation | type: boolean | description: Whether the availability is checked before creating the booking.  - `false`: A booking is only created when the slot or schedule is available. - `true`: The booking is created regardless of availability conflicts. Make sure the call's [identity](https://dev.wix.com/docs/build-apps/develop-your-app/access/about-identities.md) has the required permissions.  *Use cases for `true`:** - Emergency or priority bookings that must be accommodated. - Administrative bookings that override normal availability rules. - Testing or demonstration purposes.  Default: `false`. 
        - name: skipBusinessConfirmation | type: boolean | description: Whether `PENDING` bookings are automatically set to `CONFIRMED` for services that normally require the owner's manual confirmation.  Your app must have the `BOOKINGS.OVERRIDE_AVAILABILITY` permission when passing `true`. Default: `false`. 
        - name: skipSelectedPaymentOptionValidation | type: boolean | description: Whether customers can pay using a payment method that isn't supported for the service, but that's supported for other services.  Your app must have the `BOOKINGS.MANAGE_PAYMENTS` permission when passing `true`. Default: `false`. 
        - name: skipAddOnValidation | type: boolean | description: Whether Wix Bookings validates [add-ons](https://dev.wix.com/docs/api-reference/business-solutions/bookings/services/add-ons/introduction.md) when creating a booking. The calling [identity](https://dev.wix.com/docs/build-apps/develop-your-app/access/about-identities.md) must have `BOOKINGS.MANAGE_ADDONS` permissions to specify `true`. This allows customers to choose an add-on that's not associated with the service or choose more than the maximum number of add-ons from a group.  Default: `false`. 
   param name: formSubmission | type: formSubmission | description: Booking form data submitted by the customer during the booking process. Each key represents the name of the form submission field while the value is the data submitted by the customer for that field.  Wix Bookings stores this form data in different locations depending on the field type: - __Contact details fields__: Input values for standard contact fields such as name, email, phone, and address are saved in the booking object's `contactDetails`. - __Custom and additional fields__: All other form field values are stored separately in the [form submissions object](https://dev.wix.com/docs/rest/crm/forms/form-submissions/introduction.md).  For comprehensive details about integrating custom forms with bookings, see [Wix Forms Integration](https://dev.wix.com/docs/rest/business-solutions/bookings/wix-forms-integration.md). 
   param name: participantNotification | type: ParticipantNotification   
        - name: notifyParticipants | type: boolean | description: Whether to send a message about the changes to the customer.  Default: `false` 
        - name: message | type: string | description: Custom message to send to the participants about the changes to the booking. 
        - name: metadata | type: object | description: Information about the delivery channels used to send the notification. For example, `{"channels": "SMS" }`, `{"channels": "EMAIL" }`, or `{"channels": "EMAIL, SMS" }`. 
   param name: sendSmsReminder | type: sendSmsReminder | description: Whether to send an SMS reminder to the customer 24 hours before the session starts. The phone number is taken from `contactDetails.phone`. Default: `true`. 
 Return type: CreateBookingResponse
  - name: booking | type: Booking | description: Created booking. 
     - ONE-OF: 
        - name: totalParticipants | type: integer | description: Total number of participants. When creating a booking, use this field only if the relevant service has fixed pricing and doesn't offer [variants and options](https://dev.wix.com/docs/rest/business-solutions/bookings/services/service-options-and-variants/introduction.md). 
        - name: participantsChoices | type: ParticipantChoices | description: Information about the booked service choices and participant count for each choice. When creating a booking, use this field only if the booking includes multiple [service variants](https://dev.wix.com/docs/rest/business-solutions/bookings/services/service-options-and-variants/introduction.md).  For example, use this for a spa package booking that includes different service levels: - 2 participants chose "Standard Package". - 1 participant chose "VIP Package". 
           - name: serviceChoices | type: array<ServiceChoices> | description: Information about the booked service choices. Includes the number of participants. 
              - name: numberOfParticipants | type: integer | description: Number of participants for this [variant](https://dev.wix.com/docs/rest/business-solutions/bookings/services/service-options-and-variants/introduction.md). 
              - name: choices | type: array<ServiceChoice> | description: Service choices for these participants. 
                 - ONE-OF: 
                    - name: custom | type: string | description: Value for one of the choices in the [`CustomServiceOption.choices`](https://example.com) list. Choices are specific values for an option the customer can choose to book. For example, the option `ageGroup` may have these choices: `child`, `student`, `adult`, and `senior`. Each choice may have a different price. 
                    - name: duration | type: Duration | description:  
                       - name: minutes | type: integer | description: Duration of the service in minutes. Min: 1 minute, Max: 30 days, 23 hours, and 59 minutes 
                       - name: name | type: string | description: Name of the duration option. Defaults to the formatted duration e.g. "1 hour, 30 minutes". 
                 - name: optionId | type: string | description: GUID of the corresponding option for the choice. For example, the choice `child` could correspond to the option `ageGroup`. In this case, `optionId` is the GUID for the `ageGroup` option. 
     - name: id | type: string | description: Booking GUID. 
     - name: bookedEntity | type: BookedEntity | description: An object describing the bookable entity - either a specific time slot or a recurring schedule.  The structure depends on the type of service being booked:  __For appointment services__: Use `slot` to book a specific time slot with a service provider. Appointments are typically one-time sessions at a specific date and time.  __For class services__: Use `slot` to book a specific class session. Classes are individual sessions that can have multiple participants.  __For course services__: Use `schedule` to book an entire course consisting of multiple sessions over time. Courses are recurring, multi-session offerings.  Choose the appropriate field based on your service type and booking requirements. 
        - ONE-OF: 
           - name: slot | type: BookedSlot | description: [Booked slot](https://dev.wix.com/docs/rest/business-solutions/bookings/bookings-and-time-slots/time-slots/availability-calendar/query-availability.md).  Specify `slot` when creating bookings for: - __Appointment-based services__: Individual sessions with service providers (consultations, treatments). Wix Bookings creates a new session when the booking is confirmed. - __Class services__: Group sessions at specific times (fitness classes, workshops). Wix Bookings links the booking to an existing scheduled session.  For course services, specify `schedule` instead of `slot`. 
              - name: serviceId | type: string | description: Service GUID. 
              - name: scheduleId | type: string | description: Schedule GUID. 
              - name: eventId | type: string | description: GUID of the corresponding [event](https://dev.wix.com/docs/rest/business-management/calendar/events-v3/introduction.md). Available for both appointment and class bookings, not available for course bookings. For appointment-based services, Wix Bookings automatically populates `eventId` when the booking `status` changes to `CONFIRMED`. For class bookings, Wix Bookings automatically populates `eventId` upon booking creation. 
              - name: startDate | type: string | description: The start time of this slot in `YYYY-MM-DDThh:mm:ss`, `YYYY-MM-DDThh:mm:ss:SSS`, or `YYYY-MM-DDThh:mm:ss:SSSZZ` [ISO-8601 format](https://en.wikipedia.org/wiki/ISO_8601). For example, `2026-01-30T13:30:00`, `2026-01-30T13:30:00:000`, or `2026-01-30T13:30:00:000-05:00`. 
              - name: endDate | type: string | description: The end time of this slot in `YYYY-MM-DDThh:mm:ss`, `YYYY-MM-DDThh:mm:ss:SSS`, or `YYYY-MM-DDThh:mm:ss:SSSZZ` [ISO-8601 format](https://en.wikipedia.org/wiki/ISO_8601). For example, `2026-01-30T13:30:00`, `2026-01-30T13:30:00:000`, or `2026-01-30T13:30:00:000-05:00`. 
              - name: timezone | type: string | description: Time zone in [IANA tz database format](https://en.wikipedia.org/wiki/Tz_database). For example, `America/New_York` or `UTC`. This is the time zone in which the slot was shown to the customer at the time of booking. Wix Bookings ensures that the slot is always displayed in this same time zone to the customer, including when they view or edit their booking in the future. 
              - name: resource | type: BookedResource | description: [Primary resource](https://dev.wix.com/docs/rest/business-solutions/bookings/resources/resources-v2/introduction.md) for the booking. For example, the [staff member](https://dev.wix.com/docs/rest/business-solutions/bookings/staff-members/introduction.md) providing the service. 
                 - name: id | type: string | description: GUID of the booking's primary resource. 
                 - name: name | type: string | description: Resource's name at the time of booking. 
                 - name: email | type: string | description: Resource's email at the time of booking. 
                 - name: scheduleId | type: string | description: GUID of the schedule belonging to the booking's primary resource. 
              - name: location | type: Location | description: Location where the session takes place. 
                 - name: id | type: string | description: Business location GUID. Available only for locations that are business locations, meaning the `location_type` is `"OWNER_BUSINESS"`. 
                 - name: name | type: string | description: Location name. 
                 - name: formattedAddress | type: string | description: The full address of this location. 
                 - name: formattedAddressTranslated | type: string | description: The full translated address of this location. 
                 - name: locationType | type: LocationType | description: Location type. 
                         - enum:
                         -     UNDEFINED: Undefined location type.
                         -     OWNER_BUSINESS: The business address, as set in the site’s general settings.
                         -     OWNER_CUSTOM: The address as set when creating the service.
                         -     CUSTOM: The address as set for the individual session.
              - name: resourceSelections | type: array<ResourceSelection> | description: Information about how the customer has selected resources for the booking. Each resource type may have a different selection method. Check `resource` for resource details. 
                 - name: resourceTypeId | type: string | description: GUID of the [resource type](https://dev.wix.com/docs/api-reference/business-solutions/bookings/resources/resource-types-v2/introduction.md). 
                 - name: selectionMethod | type: SelectionMethod | description: Information about how the customer has selected the resource for this resource type. 
                         - enum:
                         -     SPECIFIC_RESOURCE: The customer explicitly chose a particular resource.
                         -     ANY_RESOURCE: The customer explicitly chose "any available resource" for this resource type.
                         -     NO_SELECTION: The customer wasn't offered a resource selection or agreement option for this resource type.
           - name: schedule | type: BookedSchedule | description: [Booked schedule](https://dev.wix.com/docs/rest/business-management/calendar/schedules-v3/introduction.md).  Specify `schedule` when creating bookings for: - __Course services__: Multi-session offerings spanning weeks or months (educational courses, training programs). Wix Bookings enrolls participants in all sessions defined by the course schedule. 
              - name: scheduleId | type: string | description: [Schedule GUID](https://dev.wix.com/docs/rest/business-management/calendar/schedules-v3/introduction.md). 
              - name: serviceId | type: string | description: Booked service GUID. 
              - name: location | type: Location | description: [Location](https://dev.wix.com/docs/rest/business-management/locations/introduction.md) where the schedule's sessions take place. 
              - name: timezone | type: string | description: Time zone in [IANA tz database format](https://en.wikipedia.org/wiki/Tz_database). For example, `America/New_York` or `UTC`. This is the time zone in which the schedule was shown to the customer at the time of booking. Wix Bookings ensures that the schedule is always displayed in this same time zone to the customer, including when they view or edit their booking in the future. 
              - name: firstSessionStart | type: string | description: Start time of the first session related to the booking in `YYYY-MM-DDThh:mm:ss`, `YYYY-MM-DDThh:mm:ss:SSS`, or `YYYY-MM-DDThh:mm:ss:SSSZZ` [ISO-8601 format](https://en.wikipedia.org/wiki/ISO_8601). For example, `2026-01-30T13:30:00`, `2026-01-30T13:30:00:000`, or `2026-01-30T13:30:00:000-05:00`. 
              - name: lastSessionEnd | type: string | description: End time of the last session related to the booking in `YYYY-MM-DDThh:mm:ss`, `YYYY-MM-DDThh:mm:ss:SSS`, or `YYYY-MM-DDThh:mm:ss:SSSZZ` [ISO-8601 format](https://en.wikipedia.org/wiki/ISO_8601). For example, `2026-01-30T13:30:00`, `2026-01-30T13:30:00:000`, or `2026-01-30T13:30:00:000-05:00`. 
        - name: title | type: string | description: Session title at the time of booking. If there is no pre-existing session, for example for appointment-based services, Wix Bookings sets `title` to the service name. 
        - name: tags | type: array | description: List of tags for the booking.  - "INDIVIDUAL": For bookings of appointment-based services. Including when the appointment is for a group of participants. - "GROUP": For bookings of individual class sessions. - "COURSE": For course bookings. 
     - name: contactDetails | type: ContactDetails | description: Contact details of the site visitor or [member](https://dev.wix.com/docs/api-reference/crm/members-contacts/members/members/introduction.md) making the booking. 
        - name: contactId | type: string | description: Contact GUID. 
        - name: firstName | type: string | description: Contact's first name. When populated from a standard booking form, this property corresponds to the `name` field. 
        - name: lastName | type: string | description: Contact's last name. 
        - name: email | type: string | description: Contact's email. If no [contact](https://dev.wix.com/docs/rest/crm/members-contacts/contacts/contacts/contact-v4/contact-object.md) with this email exist, a new contact is created. Used to validate coupon usage limitations per contact. If not specified, the coupon usage limitation will not be enforced. (Coupon usage limitation validation is not supported yet). 
        - name: phone | type: string | description: Contact's phone number. 
        - name: fullAddress | type: Address | description: Contact's full address. 
           - ONE-OF: 
              - name: streetAddress | type: StreetAddress | description: Street name, number and apartment number. 
                 - name: number | type: string | description: Street number. 
                 - name: name | type: string | description: Street name. 
                 - name: apt | type: string | description: Apartment number. 
              - name: addressLine | type: string | description: Main address line, usually street and number, as free text. 
           - name: country | type: string | description: Country code. 
           - name: subdivision | type: string | description: Subdivision. Usually state, region, prefecture or province code, according to [ISO 3166-2](https://en.wikipedia.org/wiki/ISO_3166-2). 
           - name: city | type: string | description: City name. 
           - name: postalCode | type: string | description: Zip/postal code. 
           - name: addressLine2 | type: string | description: Free text providing more detailed address info. Usually contains Apt, Suite, and Floor. 
           - name: formattedAddress | type: string | description: A string containing the full address of this location. 
           - name: hint | type: string | description: Free text to help find the address. 
           - name: geocode | type: AddressLocation | description: Coordinates of the physical address. 
              - name: latitude | type: number | description: Address latitude. 
              - name: longitude | type: number | description: Address longitude. 
           - name: countryFullname | type: string | description: Country full name. 
           - name: subdivisions | type: array<Subdivision> | description: Multi-level subdivisions from top to bottom. 
              - name: code | type: string | description: Subdivision code. Usually state, region, prefecture or province code, according to [ISO 3166-2](https://en.wikipedia.org/wiki/ISO_3166-2). 
              - name: name | type: string | description: Subdivision full name. 
        - name: countryCode | type: string | description: Contact's country in [ISO 3166-1 alpha-2 code](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) format. 
     - name: status | type: BookingStatus | description: Booking status. A booking is automatically confirmed if the service allows it and an eCommerce order is created. It is automatically declined if there is a double booking and the customer hasn't paid or is eligible for an automatic refund. Currently, only payments with pricing plans are automatically refundable. 
         - enum:
         -     CREATED: The booking was created, but the customer hasn't completed the related eCommerce order yet.
         -     CONFIRMED: The merchant has confirmed the booking and it appears in the business calendar. Merchants can set up their [services](https://dev.wix.com/docs/rest/business-solutions/bookings/services/services-v2/introduction.md) to automatically confirm all `PENDING` bookings.
         -     CANCELED: The customer has canceled the booking. Depending on the relevant service's [policy snapshot](https://dev.wix.com/docs/rest/business-solutions/bookings/policies/booking-policy-snapshots/introduction.md) they may have to pay a [cancellation fee](https://dev.wix.com/docs/rest/business-solutions/bookings/pricing/booking-fees/introduction.md).
         -     PENDING: The merchant must manually confirm the booking before it appears in the business calendar.
         -     DECLINED: The merchant has declined the booking before the customer was charged.
         -     WAITING_LIST: Currently, you can't call [Register to Waitlist](https://dev.wix.com/docs/rest/business-solutions/bookings/bookings/waitlist/register-to-waitlist.md) for course or appointment bookings, even though this is supported in live sites.
     - name: paymentStatus | type: PaymentStatus | description: The payment status of the booking. This field automatically syncs with the `paymentStatus` of the corresponding [eCommerce order](https://dev.wix.com/docs/api-reference/business-solutions/e-commerce/orders/introduction.md) when customers use Wix eCommerce checkout.  ### Integration patterns  __When using Wix eCommerce checkout__: Wix Bookings automatically syncs the payment status based on the eCommerce order's payment status. Do not manually update this field.  __When using custom payment flows__: You can manually update the payment status with [Confirm Booking or Decline Booking](https://dev.wix.com/docs/api-reference/business-solutions/bookings/bookings/bookings-writer-v2/confirm-or-decline-booking.md) to reflect the customer's payment state.  __For membership/pricing plan payments__: Wix Bookings automatically manages the payment status when customers pay with an active [pricing plan](https://dev.wix.com/docs/api-reference/business-solutions/pricing-plans/pricing-plans/introduction.md) subscription.  All payment statuses are supported for every booking `status`. 
         - enum:
         -     UNDEFINED: Undefined payment status.
         -     NOT_PAID: The booking isn't paid.
         -     PAID: The booking is fully paid.
         -     PARTIALLY_PAID: The booking is partially paid.
         -     REFUNDED: The booking is refunded.
         -     EXEMPT: The booking is free of charge.
     - name: selectedPaymentOption | type: SelectedPaymentOption | description: Payment option selected by the customer. If the customer hasn't completed their checkout, they may still change the payment method. Must be one of the payment options offered by the [service](https://dev.wix.com/docs/api-reference/business-solutions/bookings/services/services-v2/introduction.md), unless `skipSelectedPaymentOptionValidation` is `true`.  When the customer pays with a [Wix eCommerce checkout](https://dev.wix.com/docs/api-reference/business-solutions/e-commerce/checkout/introduction.md), this field is required. Otherwise, the Create Booking call fails. For custom checkouts, you don't have to specify this field. 
         - enum:
         -     UNDEFINED: Undefined payment option.
         -     OFFLINE: Offline payment.
         -     ONLINE: Online payment.
         -     MEMBERSHIP: Payment using a Wix Pricing Plan.
         -     MEMBERSHIP_OFFLINE: Customers can pay only in person with a Wix Pricing Plan, while the Wix user must manually redeem the pricing plan in the dashboard.
     - name: createdDate | type: string | description: Date and time the booking was created in `YYYY-MM-DDThh:mm:ss.sssZ` format. 
     - name: externalUserId | type: string | description: External user GUID that you can provide. 
     - name: revision | type: string | description: Revision number to be used when updating, rescheduling, or cancelling the booking. Increments by 1 each time the booking is updated, rescheduled, or canceled. To prevent conflicting changes, the current revision must be specified when updating the booking. 
     - name: createdBy | type: IdentificationData | description: GUID of the creator of the booking. If `appId` and another GUID are present, the other GUID takes precedence. 
        - ONE-OF: 
           - name: anonymousVisitorId | type: string | description: GUID of a site visitor that has not logged in to the site. 
           - name: memberId | type: string | description: GUID of a site visitor that has logged in to the site. 
           - name: wixUserId | type: string | description: GUID of a Wix user (site owner, contributor, etc.). 
           - name: appId | type: string | description: GUID of an app. 
        - name: contactId | type: string | description: GUID of of a contact in the site's [CRM by Ascend](https://www.wix.com/ascend/crm) system. 
     - name: startDate | type: string | description: The start date of the booking in `YYYY-MM-DDThh:mm:ss.sssZ` format. For a slot, this is the start date of the slot. For a schedule, this is the start date of the first session. 
     - name: endDate | type: string | description: The end date of the booking in `YYYY-MM-DDThh:mm:ss.sssZ` format. For a slot, this is the end date of the slot. For a schedule, this is the end date of the last session. 
     - name: updatedDate | type: string | description: Date and time the booking was updated in `YYYY-MM-DDThh:mm:ss.sssZ` format. 
     - name: extendedFields | type: ExtendedFields | description: Custom field data for this object. Extended fields must be configured in the app dashboard before they can be accessed with API calls. 
        - name: namespaces | type: object | description: Extended field data. Each key corresponds to the namespace of the app that created the extended fields. The value of each key is structured according to the schema defined when the extended fields were configured.  You can only access fields for which you have the appropriate permissions.  Learn more about [extended fields](https://dev.wix.com/docs/rest/articles/getting-started/extended-fields.md). 
     - name: doubleBooked | type: boolean | description: Whether this booking overlaps with another confirmed booking. Returned only if set to `true`. 
     - name: formSubmissionId | type: string | description: GUID of the [form submission](https://dev.wix.com/docs/rest/crm/forms/form-submissions/introduction.md) associated with this booking. 
     - name: formId | type: string | description: GUID of the [form](https://dev.wix.com/docs/rest/crm/forms/form-schemas/form-object.md) associated with this booking. The value depends on how the booking was created: - For bookings created with Create Booking or Bulk Create Booking, `formId` is identical to GUID of the booking form that's associated with the relevant service. - For bookings created via Create Multi Service Booking, `formId` is set to `00000000-0000-0000-0000-000000000000` (the default booking form GUID). 
     - name: bookedAddOns | type: array<BookedAddOn> | description: List of [add-ons](https://dev.wix.com/docs/api-reference/business-solutions/bookings/services/add-ons/introduction.md) associated with the booking. 
        - name: id | type: string | description: The GUID of the add-on. 
        - name: groupId | type: string | description: The GUID of the add-on group. 
        - name: durationInMinutes | type: integer | description: The add-on duration in minutes at the time of booking. Populated for duration-based add-ons. 
        - name: quantity | type: integer | description: The quantity of booked add-ons. For duration-based add-ons, `quantity` is not applicable. If `quantity` is provided as `1` for a duration-based add-on, it will be accepted but the value will be cleared. If any other value is provided, an `INVALID_ARGUMENT` error will be returned with the message: "Invalid AddOn details: either duration or quantity must be set correctly". 
        - name: name | type: string | description: Add-on `name` at the time of booking. 
        - name: nameTranslated | type: string | description: Add-on name translated to the language the customer used during booking. 
     - name: appId | type: string | description: GUID of the app that's associated with the booking. Inherited from the `appId` of the service associated with the booking. Bookings are displayed in Wix Bookings only if they are associated with the Wix Bookings app GUID or have no associated app GUID. For bookings from Wix apps, the following values apply: - Wix Bookings: `"13d21c63-b5ec-5912-8397-c3a5ddb27a97"` - Wix Services: `"cc552162-24a4-45e0-9695-230c4931ef40"` - Wix Meetings: `"6646a75c-2027-4f49-976c-58f3d713ed0f"` [Full list of apps created by Wix](https://dev.wix.com/docs/api-reference/articles/work-with-wix-apis/platform/about-apps-created-by-wix.md). <!-- TODO: Uncomment when Platform docs are published - Learn more about [app identity in the Bookings Platform](https://dev.wix.com/docs/api-reference/business-solutions/bookings/bookings-platform/app-identity-in-the-bookings-platform.md). --> 
     - name: createdByAppId | type: string | description: GUID of the app that created the booking. This field is used for analytics, auditing, and tracking creation sources. This read-only field is automatically populated during booking creation by checking these sources in order: 1. The caller's App GUID from the request identity context (external app or server identity). 2. The booking's `appId` field (inherited from the service's `appId`). 3. The Wix Bookings App GUID (`13d21c63-b5ec-5912-8397-c3a5ddb27a97`) as the final fallback. <!-- TODO: Uncomment when Platform docs are published - Learn more about [app identity in the Bookings Platform](https://dev.wix.com/docs/api-reference/business-solutions/bookings/bookings-platform/app-identity-in-the-bookings-platform.md). --> 
     - name: depositSelected | type: boolean | description: Whether the customer chooses to pay only the deposit amount upfront.  - `true`: The customer pays only the deposit amount upfront. - `false`: The customer pays the full price upfront.  Used only when `selectedPaymentOption` is `ONLINE` and the [service](https://dev.wix.com/docs/api-reference/business-solutions/bookings/services/services-v2/introduction.md) has a deposit amount set.  When the service supports deposit payments and `fullUpfrontPaymentAllowed` is `false`, this field must be `true`. When the service supports deposit payments and `fullUpfrontPaymentAllowed` is `true`, this field can be `true` or `false`. 

 Possible Errors:
   HTTP Code: 400 | Status Code: INVALID_ARGUMENT | Application Code: CONTACT_DETAILS_CONFLICT | Description: Contact details in the booking don't match the form submission. Ensure contactDetails and formSubmission have matching email, phone, and name values.
   HTTP Code: 400 | Status Code: INVALID_ARGUMENT | Application Code: INVALID_TIME_ZONE | Description: The time zone is invalid. Provide a valid IANA time zone identifier.
   HTTP Code: 400 | Status Code: INVALID_ARGUMENT | Application Code: INVALID_DATE_FORMAT | Description: The date format is invalid. Use the format `YYYY-MM-DDThh:mm:ss` in ISO-8601 format.
   HTTP Code: 400 | Status Code: INVALID_ARGUMENT | Application Code: INVALID_CHOICES | Description: The specified choices are invalid. Provide valid service option choices.
   HTTP Code: 403 | Status Code: PERMISSION_DENIED | Application Code: UNAUTHORIZED_OPERATION | Description: The [identity](https://dev.wix.com/docs/api-reference/articles/authentication/about-identities.md) used to call the method doesn't have the required permissions.
   HTTP Code: 403 | Status Code: PERMISSION_DENIED | Application Code: BOOKING_POLICY_VIOLATION | Description: The booking violates the service's booking policy. Check booking window restrictions, advance notice requirements, or scheduling rules.
   HTTP Code: 428 | Status Code: FAILED_PRECONDITION | Application Code: CAN_NOT_SKIP_AVAILABILITY_VALIDATION_IF_RESOURCE_NOT_PROVIDED | Description: Can't skip availability validation when no resource is provided. Specify a resource or remove the skip flag.
   HTTP Code: 428 | Status Code: FAILED_PRECONDITION | Application Code: CAN_NOT_CREATE_BOOKING_WITH_MULTI_SERVICE_BOOKING_INFO | Description: Can't create a single booking with multi-service booking information. Use the multi-service booking method instead.
   HTTP Code: 428 | Status Code: FAILED_PRECONDITION | Application Code: INVALID_FLOW_SELECTED_RESOURCES | Description: The selected resources are invalid for this booking flow. Verify the resources match the service requirements.
   HTTP Code: 428 | Status Code: FAILED_PRECONDITION | Application Code: INVALID_SERVICE_CHOICES | Description: The specified service choices are invalid. Verify the choices match the service's supported options and variants.
   HTTP Code: 428 | Status Code: FAILED_PRECONDITION | Application Code: FAILED_VALIDATING_AVAILABILITY | Description: Availability validation failed. The requested time slot or schedule may be fully booked or unavailable.
   HTTP Code: 428 | Status Code: FAILED_PRECONDITION | Application Code: SLOT_NOT_AVAILABLE | Description: The slot is no longer available for booking. It may have been booked by another customer or is outside business hours.
   HTTP Code: 428 | Status Code: FAILED_PRECONDITION | Application Code: SCHEDULE_CAPACITY_EXCEEDED | Description: The schedule capacity was exceeded. The requested number of participants exceeds available capacity.
   HTTP Code: 428 | Status Code: FAILED_PRECONDITION | Application Code: SESSION_CAPACITY_EXCEEDED | Description: The session capacity was exceeded. The requested number of participants exceeds available capacity.
   HTTP Code: 428 | Status Code: FAILED_PRECONDITION | Application Code: VALIDATION_FAILURE | Description: Validation failed. Verify all required booking fields are provided and valid.
   HTTP Code: 428 | Status Code: FAILED_PRECONDITION | Application Code: FAILED_RESOLVING_CUSTOM_CHOICES | Description: Couldn't resolve the specified service choices. Verify the choices are valid for this service.
   HTTP Code: 428 | Status Code: FAILED_PRECONDITION | Application Code: SCHEDULE_NOT_FOUND | Description: The specified schedule doesn't exist. Verify the schedule GUID is correct.
   HTTP Code: 428 | Status Code: FAILED_PRECONDITION | Application Code: SESSION_NOT_FOUND | Description: The specified session doesn't exist. Verify the session GUID is correct.


```

### Examples

### Create an appointment booking
```curl
curl -X POST \
'https://www.wixapis.com/bookings/v2/bookings' \
-H 'Authorization: <AUTH>' \
-d '{
  "booking": {
    "bookedEntity": {
      "slot": {
        "serviceId": "8ee826a3-64c4-416d-a22c-e01d39f56931",
        "scheduleId": "844772a6-ad31-49fb-b3d9-7aef1e559b7e",
        "startDate": "2022-12-26T12:00:00.000Z",
        "endDate": "2022-12-26T13:00:00.000Z",
        "timezone": "Europe/Dublin",
        "resource": {
          "id": "5fa50f19-4c94-4c42-a72b-289505ba2028",
          "name": "Tom Jones",
          "scheduleId": "a4166c1f-728c-4895-8a6e-1942bb321315"
        },
        "location": {
          "id": "9de094d5-8985-484e-9218-d020d9d17953",
          "name": "Location Name",
          "formattedAddress": "Location Address",
          "locationType": "OWNER_BUSINESS"
        }
      },
      "title": "In-person Appointment",
      "tags": [
        "INDIVIDUAL"
      ]
    },
    "contactDetails": {
       "firstName": "John",
       "email": "john@example.com"
    },
    "additionalFields": [],
    "totalParticipants": 1,
    "selectedPaymentOption": "ONLINE"
  },
  "sendSmsReminder": false,
  "participantNotification": {
    "notifyParticipants": true
  },
  "flowControlSettings": {
    "skipAvailabilityValidation": false,
    "skipBusinessConfirmation": false,
    "skipSelectedPaymentOptionValidation": false
  }
}'
```

### Create a course booking
```curl
curl -X POST \
'https://www.wixapis.com/bookings/v2/bookings' \
-H 'Authorization: <AUTH>' \
-d '{
  "booking": {
    "bookedEntity": {
      "schedule": {
        "scheduleId": "7935f7bd-4aa5-4402-9d2f-2f4a7c039c54",
        "serviceId": "4d92514a-73ef-4477-8e4b-51d67c18c652",
        "location": {
          "name": "Location Name",
          "formattedAddress": "Location Address",
          "locationType": "OWNER_BUSINESS"
        },
        "timezone": "Europe/Dublin",
        "firstSessionStart": "2022-09-30T14:00:00.000+01:00",
        "lastSessionEnd": "2022-12-30T15:00:00.000Z"
      },
      "title": "Future Group Trainings",
      "tags": [
        "COURSE"
      ]
    },
    "contactDetails": {
      "firstName": "John",
      "email": "john@example.com"
    },
    "additionalFields": [],
    "totalParticipants": 1,
    "selectedPaymentOption": "ONLINE"
  },
  "sendSmsReminder": false,
  "participantNotification": {
    "notifyParticipants": true
  },
  "flowControlSettings": {
    "skipAvailabilityValidation": false,
    "skipBusinessConfirmation": false,
    "skipSelectedPaymentOptionValidation": false
  }
}'
```

### Create a class session booking
```curl
curl -X POST \
'https://www.wixapis.com/bookings/v2/bookings' \
-H 'Authorization: <AUTH>' \
-d '{
  "booking": {
    "bookedEntity": {
      "slot": {
        "sessionId": "193ZPR9ppP9emJUCLevcLf6orynNEIDt5nc0520xjGQILnPPaF5s62yK3BWz7ExgIRM1Grhufc19yxtld2ty3Xr5MpSWDTKOTjNUxnPiSzuHshes69npqrfSSRCiPbJmW985sUnh3XKhP9BqJdfRknRxJib3BqXo8LrA5kdngb4ubOZQ9d6yW73HMpiWrBufouhn4UalWsPk1OQQpysed4Vo0hq0E8KuD3nw9VMDdBToFyfp8RNAepDdgfBCfIJ3SEYOjyS4rvQAovUxmUA3xeRaV35f1yl8cth0ZZQuLx4gUrle5ciKpRmWU9TM9k5upRk9NyDw3OD9Zd",
        "serviceId": "8bdfb0dc-9461-4f21-b576-f866f9f50dfb",
        "scheduleId": "1b5e8844-7d10-42a3-b326-87941e5efdcb",
        "startDate": "2022-12-28T14:00:00.000Z",
        "endDate": "2022-12-28T15:00:00.000Z",
        "timezone": "Europe/Dublin",
        "resource": {
          "id": "64bb860a-eda5-4992-9fc6-538d58e818ec",
          "name": "Sam Kruger",
          "scheduleId": "2bc4bf60-cccb-42ce-a43d-05d1bbbfac4c"
        },
        "location": {
          "id": "9de094d5-8985-484e-9218-d020d9d17953",
          "name": "Location Name",
          "formattedAddress": "Location Address",
          "locationType": "OWNER_BUSINESS"
        }
      },
      "title": "CLASS",
      "tags": [
        "GROUP"
      ]
    },
    "contactDetails": {
      "firstName": "John",
      "email": "john@example.com"
    },
    "additionalFields": [],
    "totalParticipants": 1,
    "selectedPaymentOption": "ONLINE"
  },
  "sendSmsReminder": false,
  "participantNotification": {
    "notifyParticipants": true
  },
  "flowControlSettings": {
    "skipAvailabilityValidation": false,
    "skipBusinessConfirmation": false,
    "skipSelectedPaymentOptionValidation": false
  }
}'
```

---

## JavaScript SDK

### Schema

```
 Method: wixClientAdmin.bookings.Bookings.createBooking(booking, options)
 Description: Creates a booking.   ### Appointment booking  For appointment-based services, specify the relevant time slot in `bookedEntity.slot`.  We recommend following the [appointment booking sample flow](https://dev.wix.com/docs/api-reference/business-solutions/bookings/bookings/bookings-writer-v2/sample-flows.md#book-an-appointment) using Time Slots V2. Specify the slot's `startDate`, `endDate`, `resource`, and `location` in `booking.bookedEntity.slot`.  ### Class session booking  For class services, specify the relevant event GUID as `bookedEntity.slot.eventId`.  We recommend following the [class session booking sample flow](https://dev.wix.com/docs/api-reference/business-solutions/bookings/bookings/bookings-writer-v2/sample-flows.md#book-a-class-session) using Time Slots V2. Specify the `eventId` from the selected time slot in `booking.bookedEntity.slot.eventId`.  When you specify `eventId`, Wix Bookings automatically derives `startDate`, `endDate`, `timezone`, `resource`, and `location` based on the event details. Manually specified values are ignored.  ### Course booking  For course services, specify the course's schedule GUID in `bookedEntity.schedule.scheduleId`. We recommend following [this sample flow](https://dev.wix.com/docs/rest/business-solutions/bookings/end-to-end-booking-flows.md#book-a-course) to minimize failed calls due to unavailability.  ### Booking status  Create Booking defaults to `status=CREATED`. Such bookings aren't visible in the [Booking Calendar](https://support.wix.com/en/article/wix-bookings-about-the-wix-booking-calendar).  Only [identities](https://dev.wix.com/docs/build-apps/develop-your-app/access/about-identities.md) with `Manage Bookings` permissions can set `status=CONFIRMED`.  ### Related resources  Specifying a `resource` triggers an availability check, and the Create Booking call fails if the resource is unavailable.  If you omit `resource`, resource assignment and availability validation occur during booking confirmation. If no resources are available, the behavior depends on the confirmation method used and payment status.  ### Booking form data  When customers sign up for a service, they must fill out the [booking form](https://support.wix.com/en/article/wix-bookings-creating-and-setting-up-your-booking-forms). To create a booking with a completed booking form, specify the relevant data in `formSubmission`. When specifying `formSubmission`, Wix Bookings sets all `booking.contactDetails` fields based on `formSubmission` and ignores any values in `booking.contactDetails`, except for `booking.contactDetails.contactId`. To avoid conflicts, send `booking.contactDetails.contactId` together with `formSubmission`, and omit other contact details. Learn more about the [Bookings and Wix Forms integration](https://dev.wix.com/docs/rest/business-solutions/bookings/wix-forms-integration.md).  ### Participant information  You must specify either `participantsChoices` or `totalParticipants`. The call fails if the specified `participantsChoices` aren't among the supported [service options and variants](https://dev.wix.com/docs/rest/business-solutions/bookings/services/service-options-and-variants/introduction.md).  ### Add-ons  You can include [add-ons](https://dev.wix.com/docs/api-reference/business-solutions/bookings/services/add-ons/introduction.md) when creating a booking by specifying `bookedAddOns`. Each selected add-on must belong to an [add-on group](https://dev.wix.com/docs/api-reference/business-solutions/bookings/services/services-v2/about-add-on-groups.md) associated with the service and respect the group's selection limits.  ### Notify customers  You can specify a `participantNotification.message` for the customer that's send immediately. Ensure `participantNotification.notifyParticipants` is set to `true` to send the message.  If you specify `{"sendSmsReminder": true}`, the customer receives an SMS 24 hours before the session starts. The phone number is taken from `contactDetails.phone`.  ### Payment options  The specified `selectedPaymentOption` indicates how the customer intends to pay, allowing for later changes to a different method supported by the service.  When the customer pays with a [Wix eCommerce checkout](https://dev.wix.com/docs/api-reference/business-solutions/e-commerce/purchase-flow/checkout/introduction.md), you must specify a `selectedPaymentOption`. Otherwise, the Create Booking call fails. For custom checkouts, you don't have to specify a `selectedPaymentOption`.  ### Payment status  All bookings are created with `paymentStatus=UNDEFINED`, ignoring the payment status you specify.  For customers paying with a [Wix eCommerce checkout](https://dev.wix.com/docs/rest/business-solutions/e-commerce/purchase-flow/checkout/checkout/introduction.md), Wix Bookings automatically syncs the booking's payment status from the corresponding [eCommerce order](https://dev.wix.com/docs/rest/business-solutions/e-commerce/orders/introduction.md).  For customers using a custom checkout, call [Confirm or Decline Booking](https://dev.wix.com/docs/rest/business-solutions/bookings/bookings/bookings-writer-v2/confirm-or-decline-booking.md) to update booking's payment status manually.  ### Admin overwrites  There are small but important differences when you specify special `flowControlSettings`:  - `{"skipAvailabilityValidation": true}`: The call succeeds regardless of availability. If you don't specify any resource, the call succeeds even if no resource of the relevant type is available. - `{"skipBusinessConfirmation": true}`: Automatically confirms `PENDING` bookings that require manual confirmation. - `{"skipSelectedPaymentOptionValidation": true}`: Allows customers to pay with payment methods that aren't supported for the service. - `{"skipAddOnValidation": true}`: Allows customers to choose add-ons that aren't associated with the service or exceed group selection limits. - `{"allowAddOnChanges": true}`: Allows customers to update the list of add-ons associated with the booking when rescheduling.  When using special `flowControlSettings`, ensure you have sufficient permissions. If you encounter failed calls due to insufficient permissions, consider the following options:  - **App developers** can use a higher [permission](https://dev.wix.com/docs/build-apps/develop-your-app/access/authorization/about-permissions.md), such as `MANAGE BOOKINGS - ALL PERMISSIONS`. - **Site developers** can utilize [elevation](https://dev.wix.com/docs/develop-websites/articles/coding-with-velo/authorization/elevation.md).  Granting additional permissions and using elevation permits method calls that would typically fail due to authorization checks. Therefore, you should use them intentionally and securely.
 Required parameters: booking, booking.bookedEntity, booking.additionalFields._id
 Method parameters: 
   param name: booking | type: Booking | description: An entity representing a scheduled appointment, class session, or course. | required: true
    - ONE-OF: - required: true
     - name: totalParticipants | type: integer | description: Total number of participants. When creating a booking, use this field only if the relevant service has fixed pricing and doesn't offer [variants and options](https://dev.wix.com/docs/rest/business-solutions/bookings/services/service-options-and-variants/introduction.md). 
     - name: participantsChoices | type: ParticipantChoices | description: Information about the booked service choices and participant count for each choice. When creating a booking, use this field only if the booking includes multiple [service variants](https://dev.wix.com/docs/rest/business-solutions/bookings/services/service-options-and-variants/introduction.md).  For example, use this for a spa package booking that includes different service levels: - 2 participants chose "Standard Package". - 1 participant chose "VIP Package". 
        - name: serviceChoices | type: array<ServiceChoices> | description: Information about the booked service choices. Includes the number of participants. 
           - name: numberOfParticipants | type: integer | description: Number of participants for this [variant](https://dev.wix.com/docs/rest/business-solutions/bookings/services/service-options-and-variants/introduction.md). 
           - name: choices | type: array<ServiceChoice> | description: Service choices for these participants. 
              - ONE-OF: 
                 - name: custom | type: string | description: Value for one of the choices in the [`CustomServiceOption.choices`](https://example.com) list. Choices are specific values for an option the customer can choose to book. For example, the option `ageGroup` may have these choices: `child`, `student`, `adult`, and `senior`. Each choice may have a different price. 
                 - name: duration | type: Duration | description:  
                    - name: minutes | type: integer | description: Duration of the service in minutes. Min: 1 minute, Max: 30 days, 23 hours, and 59 minutes 
                    - name: name | type: string | description: Name of the duration option. Defaults to the formatted duration e.g. "1 hour, 30 minutes". 
              - name: optionId | type: string | description: GUID of the corresponding option for the choice. For example, the choice `child` could correspond to the option `ageGroup`. In this case, `optionId` is the GUID for the `ageGroup` option. 
        - name: bookedEntity | type: BookedEntity | description: An object describing the bookable entity - either a specific time slot or a recurring schedule.  The structure depends on the type of service being booked:  __For appointment services__: Use `slot` to book a specific time slot with a service provider. Appointments are typically one-time sessions at a specific date and time.  __For class services__: Use `slot` to book a specific class session. Classes are individual sessions that can have multiple participants.  __For course services__: Use `schedule` to book an entire course consisting of multiple sessions over time. Courses are recurring, multi-session offerings.  Choose the appropriate field based on your service type and booking requirements. | required: true
           - ONE-OF: - required: true
              - name: slot | type: BookedSlot | description: [Booked slot](https://dev.wix.com/docs/rest/business-solutions/bookings/bookings-and-time-slots/time-slots/availability-calendar/query-availability.md).  Specify `slot` when creating bookings for: - __Appointment-based services__: Individual sessions with service providers (consultations, treatments). Wix Bookings creates a new session when the booking is confirmed. - __Class services__: Group sessions at specific times (fitness classes, workshops). Wix Bookings links the booking to an existing scheduled session.  For course services, specify `schedule` instead of `slot`. 
                 - name: serviceId | type: string | description: Service GUID. 
                 - name: scheduleId | type: string | description: Schedule GUID. 
                 - name: eventId | type: string | description: GUID of the corresponding [event](https://dev.wix.com/docs/rest/business-management/calendar/events-v3/introduction.md). Available for both appointment and class bookings, not available for course bookings. For appointment-based services, Wix Bookings automatically populates `eventId` when the booking `status` changes to `CONFIRMED`. For class bookings, Wix Bookings automatically populates `eventId` upon booking creation. 
                 - name: startDate | type: string | description: The start time of this slot in `YYYY-MM-DDThh:mm:ss`, `YYYY-MM-DDThh:mm:ss:SSS`, or `YYYY-MM-DDThh:mm:ss:SSSZZ` [ISO-8601 format](https://en.wikipedia.org/wiki/ISO_8601). For example, `2026-01-30T13:30:00`, `2026-01-30T13:30:00:000`, or `2026-01-30T13:30:00:000-05:00`. 
                 - name: endDate | type: string | description: The end time of this slot in `YYYY-MM-DDThh:mm:ss`, `YYYY-MM-DDThh:mm:ss:SSS`, or `YYYY-MM-DDThh:mm:ss:SSSZZ` [ISO-8601 format](https://en.wikipedia.org/wiki/ISO_8601). For example, `2026-01-30T13:30:00`, `2026-01-30T13:30:00:000`, or `2026-01-30T13:30:00:000-05:00`. 
                 - name: timezone | type: string | description: Time zone in [IANA tz database format](https://en.wikipedia.org/wiki/Tz_database). For example, `America/New_York` or `UTC`. This is the time zone in which the slot was shown to the customer at the time of booking. Wix Bookings ensures that the slot is always displayed in this same time zone to the customer, including when they view or edit their booking in the future. 
                 - name: resource | type: BookedResource | description: [Primary resource](https://dev.wix.com/docs/rest/business-solutions/bookings/resources/resources-v2/introduction.md) for the booking. For example, the [staff member](https://dev.wix.com/docs/rest/business-solutions/bookings/staff-members/introduction.md) providing the service. 
                    - name: _id | type: string | description: GUID of the booking's primary resource. 
                    - name: name | type: string | description: Resource's name at the time of booking. 
                    - name: email | type: string | description: Resource's email at the time of booking. 
                    - name: scheduleId | type: string | description: GUID of the schedule belonging to the booking's primary resource. 
                 - name: location | type: Location | description: Location where the session takes place. 
                    - name: _id | type: string | description: Business location GUID. Available only for locations that are business locations, meaning the `location_type` is `"OWNER_BUSINESS"`. 
                    - name: name | type: string | description: Location name. 
                    - name: formattedAddress | type: string | description: The full address of this location. 
                    - name: formattedAddressTranslated | type: string | description: The full translated address of this location. 
                    - name: locationType | type: LocationType | description: Location type. 
                             - enum:
                             -     UNDEFINED: Undefined location type.
                             -     OWNER_BUSINESS: The business address, as set in the site’s general settings.
                             -     OWNER_CUSTOM: The address as set when creating the service.
                             -     CUSTOM: The address as set for the individual session.
                 - name: resourceSelections | type: array<ResourceSelection> | description: Information about how the customer has selected resources for the booking. Each resource type may have a different selection method. Check `resource` for resource details. 
                    - name: resourceTypeId | type: string | description: GUID of the [resource type](https://dev.wix.com/docs/api-reference/business-solutions/bookings/resources/resource-types-v2/introduction.md). 
                    - name: selectionMethod | type: SelectionMethod | description: Information about how the customer has selected the resource for this resource type. 
                             - enum:
                             -     SPECIFIC_RESOURCE: The customer explicitly chose a particular resource.
                             -     ANY_RESOURCE: The customer explicitly chose "any available resource" for this resource type.
                             -     NO_SELECTION: The customer wasn't offered a resource selection or agreement option for this resource type.
              - name: schedule | type: BookedSchedule | description: [Booked schedule](https://dev.wix.com/docs/rest/business-management/calendar/schedules-v3/introduction.md).  Specify `schedule` when creating bookings for: - __Course services__: Multi-session offerings spanning weeks or months (educational courses, training programs). Wix Bookings enrolls participants in all sessions defined by the course schedule. 
                 - name: scheduleId | type: string | description: [Schedule GUID](https://dev.wix.com/docs/rest/business-management/calendar/schedules-v3/introduction.md). 
                 - name: serviceId | type: string | description: Booked service GUID. 
                 - name: timezone | type: string | description: Time zone in [IANA tz database format](https://en.wikipedia.org/wiki/Tz_database). For example, `America/New_York` or `UTC`. This is the time zone in which the schedule was shown to the customer at the time of booking. Wix Bookings ensures that the schedule is always displayed in this same time zone to the customer, including when they view or edit their booking in the future. 
           - name: tags | type: array | description: List of tags for the booking.  - "INDIVIDUAL": For bookings of appointment-based services. Including when the appointment is for a group of participants. - "GROUP": For bookings of individual class sessions. - "COURSE": For course bookings. 
        - name: contactDetails | type: ContactDetails | description: Contact details of the site visitor or [member](https://dev.wix.com/docs/api-reference/crm/members-contacts/members/members/introduction.md) making the booking. 
           - name: contactId | type: string | description: Contact GUID. 
           - name: firstName | type: string | description: Contact's first name. When populated from a standard booking form, this property corresponds to the `name` field. 
           - name: lastName | type: string | description: Contact's last name. 
           - name: email | type: string | description: Contact's email. If no [contact](https://dev.wix.com/docs/rest/crm/members-contacts/contacts/contacts/contact-v4/contact-object.md) with this email exist, a new contact is created. Used to validate coupon usage limitations per contact. If not specified, the coupon usage limitation will not be enforced. (Coupon usage limitation validation is not supported yet). 
           - name: phone | type: string | description: Contact's phone number. 
           - name: fullAddress | type: Address | description: Contact's full address. 
              - ONE-OF: 
                 - name: streetAddress | type: StreetAddress | description: Street name, number and apartment number. 
                    - name: number | type: string | description: Street number. 
                    - name: name | type: string | description: Street name. 
                    - name: apt | type: string | description: Apartment number. 
                 - name: addressLine | type: string | description: Main address line, usually street and number, as free text. 
              - name: country | type: string | description: Country code. 
              - name: subdivision | type: string | description: Subdivision. Usually state, region, prefecture or province code, according to [ISO 3166-2](https://en.wikipedia.org/wiki/ISO_3166-2). 
              - name: city | type: string | description: City name. 
              - name: postalCode | type: string | description: Zip/postal code. 
              - name: addressLine2 | type: string | description: Free text providing more detailed address info. Usually contains Apt, Suite, and Floor. 
              - name: formattedAddress | type: string | description: A string containing the full address of this location. 
              - name: hint | type: string | description: Free text to help find the address. 
              - name: geocode | type: AddressLocation | description: Coordinates of the physical address. 
                 - name: latitude | type: number | description: Address latitude. 
                 - name: longitude | type: number | description: Address longitude. 
              - name: countryFullname | type: string | description: Country full name. 
              - name: subdivisions | type: array<Subdivision> | description: Multi-level subdivisions from top to bottom. 
                 - name: code | type: string | description: Subdivision code. Usually state, region, prefecture or province code, according to [ISO 3166-2](https://en.wikipedia.org/wiki/ISO_3166-2). 
                 - name: name | type: string | description: Subdivision full name. 
           - name: countryCode | type: string | description: Contact's country in [ISO 3166-1 alpha-2 code](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) format. 
        - name: status | type: BookingStatus | description: Booking status. A booking is automatically confirmed if the service allows it and an eCommerce order is created. It is automatically declined if there is a double booking and the customer hasn't paid or is eligible for an automatic refund. Currently, only payments with pricing plans are automatically refundable. 
             - enum:
             -     CREATED: The booking was created, but the customer hasn't completed the related eCommerce order yet.
             -     CONFIRMED: The merchant has confirmed the booking and it appears in the business calendar. Merchants can set up their [services](https://dev.wix.com/docs/rest/business-solutions/bookings/services/services-v2/introduction.md) to automatically confirm all `PENDING` bookings.
             -     CANCELED: The customer has canceled the booking. Depending on the relevant service's [policy snapshot](https://dev.wix.com/docs/rest/business-solutions/bookings/policies/booking-policy-snapshots/introduction.md) they may have to pay a [cancellation fee](https://dev.wix.com/docs/rest/business-solutions/bookings/pricing/booking-fees/introduction.md).
             -     PENDING: The merchant must manually confirm the booking before it appears in the business calendar.
             -     DECLINED: The merchant has declined the booking before the customer was charged.
             -     WAITING_LIST: Currently, you can't call [Register to Waitlist](https://dev.wix.com/docs/rest/business-solutions/bookings/bookings/waitlist/register-to-waitlist.md) for course or appointment bookings, even though this is supported in live sites.
        - name: paymentStatus | type: PaymentStatus | description: The payment status of the booking. This field automatically syncs with the `paymentStatus` of the corresponding [eCommerce order](https://dev.wix.com/docs/api-reference/business-solutions/e-commerce/orders/introduction.md) when customers use Wix eCommerce checkout.  ### Integration patterns  __When using Wix eCommerce checkout__: Wix Bookings automatically syncs the payment status based on the eCommerce order's payment status. Do not manually update this field.  __When using custom payment flows__: You can manually update the payment status with [Confirm Booking or Decline Booking](https://dev.wix.com/docs/api-reference/business-solutions/bookings/bookings/bookings-writer-v2/confirm-or-decline-booking.md) to reflect the customer's payment state.  __For membership/pricing plan payments__: Wix Bookings automatically manages the payment status when customers pay with an active [pricing plan](https://dev.wix.com/docs/api-reference/business-solutions/pricing-plans/pricing-plans/introduction.md) subscription.  All payment statuses are supported for every booking `status`. 
             - enum:
             -     UNDEFINED: Undefined payment status.
             -     NOT_PAID: The booking isn't paid.
             -     PAID: The booking is fully paid.
             -     PARTIALLY_PAID: The booking is partially paid.
             -     REFUNDED: The booking is refunded.
             -     EXEMPT: The booking is free of charge.
        - name: selectedPaymentOption | type: SelectedPaymentOption | description: Payment option selected by the customer. If the customer hasn't completed their checkout, they may still change the payment method. Must be one of the payment options offered by the [service](https://dev.wix.com/docs/api-reference/business-solutions/bookings/services/services-v2/introduction.md), unless `skipSelectedPaymentOptionValidation` is `true`.  When the customer pays with a [Wix eCommerce checkout](https://dev.wix.com/docs/api-reference/business-solutions/e-commerce/checkout/introduction.md), this field is required. Otherwise, the Create Booking call fails. For custom checkouts, you don't have to specify this field. 
             - enum:
             -     UNDEFINED: Undefined payment option.
             -     OFFLINE: Offline payment.
             -     ONLINE: Online payment.
             -     MEMBERSHIP: Payment using a Wix Pricing Plan.
             -     MEMBERSHIP_OFFLINE: Customers can pay only in person with a Wix Pricing Plan, while the Wix user must manually redeem the pricing plan in the dashboard.
        - name: externalUserId | type: string | description: External user GUID that you can provide. 
        - name: revision | type: string | description: Revision number to be used when updating, rescheduling, or cancelling the booking. Increments by 1 each time the booking is updated, rescheduled, or canceled. To prevent conflicting changes, the current revision must be specified when updating the booking. 
        - name: extendedFields | type: ExtendedFields | description: Custom field data for this object. Extended fields must be configured in the app dashboard before they can be accessed with API calls. 
           - name: namespaces | type: object | description: Extended field data. Each key corresponds to the namespace of the app that created the extended fields. The value of each key is structured according to the schema defined when the extended fields were configured.  You can only access fields for which you have the appropriate permissions.  Learn more about [extended fields](https://dev.wix.com/docs/rest/articles/getting-started/extended-fields.md). 
        - name: formSubmissionId | type: string | description: GUID of the [form submission](https://dev.wix.com/docs/rest/crm/forms/form-submissions/introduction.md) associated with this booking. 
        - name: bookedAddOns | type: array<BookedAddOn> | description: List of [add-ons](https://dev.wix.com/docs/api-reference/business-solutions/bookings/services/add-ons/introduction.md) associated with the booking. 
           - name: _id | type: string | description: The GUID of the add-on. 
           - name: groupId | type: string | description: The GUID of the add-on group. 
           - name: quantity | type: integer | description: The quantity of booked add-ons. For duration-based add-ons, `quantity` is not applicable. If `quantity` is provided as `1` for a duration-based add-on, it will be accepted but the value will be cleared. If any other value is provided, an `INVALID_ARGUMENT` error will be returned with the message: "Invalid AddOn details: either duration or quantity must be set correctly". 
        - name: depositSelected | type: boolean | description: Whether the customer chooses to pay only the deposit amount upfront.  - `true`: The customer pays only the deposit amount upfront. - `false`: The customer pays the full price upfront.  Used only when `selectedPaymentOption` is `ONLINE` and the [service](https://dev.wix.com/docs/api-reference/business-solutions/bookings/services/services-v2/introduction.md) has a deposit amount set.  When the service supports deposit payments and `fullUpfrontPaymentAllowed` is `false`, this field must be `true`. When the service supports deposit payments and `fullUpfrontPaymentAllowed` is `true`, this field can be `true` or `false`. 
   param name: options | type: CreateBookingOptions  none 
        - name: participantNotification | type: ParticipantNotification | description: Information about whether to notify the customer and the message to send. 
           - name: notifyParticipants | type: boolean | description: Whether to send a message about the changes to the customer.  Default: `false` 
           - name: message | type: string | description: Custom message to send to the participants about the changes to the booking. 
           - name: metadata | type: object | description: Information about the delivery channels used to send the notification. For example, `{"channels": "SMS" }`, `{"channels": "EMAIL" }`, or `{"channels": "EMAIL, SMS" }`. 
        - name: sendSmsReminder | type: boolean | description: Whether to send an SMS reminder to the customer 24 hours before the session starts. The phone number is taken from `contactDetails.phone`. Default: `true`. 
        - name: flowControlSettings | type: CreateBookingFlowControlSettings | description: Whether to ignore specific standard procedures of the Wix Bookings flow. For example, whether to check availability when creating a booking. 
           - name: skipAvailabilityValidation | type: boolean | description: Whether the availability is checked before creating the booking.  - `false`: A booking is only created when the slot or schedule is available. - `true`: The booking is created regardless of availability conflicts. Make sure the call's [identity](https://dev.wix.com/docs/build-apps/develop-your-app/access/about-identities.md) has the required permissions.  *Use cases for `true`:** - Emergency or priority bookings that must be accommodated. - Administrative bookings that override normal availability rules. - Testing or demonstration purposes.  Default: `false`. 
           - name: skipBusinessConfirmation | type: boolean | description: Whether `PENDING` bookings are automatically set to `CONFIRMED` for services that normally require the owner's manual confirmation.  Your app must have the `BOOKINGS.OVERRIDE_AVAILABILITY` permission when passing `true`. Default: `false`. 
           - name: skipSelectedPaymentOptionValidation | type: boolean | description: Whether customers can pay using a payment method that isn't supported for the service, but that's supported for other services.  Your app must have the `BOOKINGS.MANAGE_PAYMENTS` permission when passing `true`. Default: `false`. 
           - name: skipAddOnValidation | type: boolean | description: Whether Wix Bookings validates [add-ons](https://dev.wix.com/docs/api-reference/business-solutions/bookings/services/add-ons/introduction.md) when creating a booking. The calling [identity](https://dev.wix.com/docs/build-apps/develop-your-app/access/about-identities.md) must have `BOOKINGS.MANAGE_ADDONS` permissions to specify `true`. This allows customers to choose an add-on that's not associated with the service or choose more than the maximum number of add-ons from a group.  Default: `false`. 
        - name: formSubmission | type: object | description: Booking form data submitted by the customer during the booking process. Each key represents the name of the form submission field while the value is the data submitted by the customer for that field.  Wix Bookings stores this form data in different locations depending on the field type: - __Contact details fields__: Input values for standard contact fields such as name, email, phone, and address are saved in the booking object's `contactDetails`. - __Custom and additional fields__: All other form field values are stored separately in the [form submissions object](https://dev.wix.com/docs/rest/crm/forms/form-submissions/introduction.md).  For comprehensive details about integrating custom forms with bookings, see [Wix Forms Integration](https://dev.wix.com/docs/rest/business-solutions/bookings/wix-forms-integration.md). 
 Return type: PROMISE<CreateBookingResponse>
  - name: booking | type: Booking | description: Created booking. 
     - ONE-OF: 
        - name: totalParticipants | type: integer | description: Total number of participants. When creating a booking, use this field only if the relevant service has fixed pricing and doesn't offer [variants and options](https://dev.wix.com/docs/rest/business-solutions/bookings/services/service-options-and-variants/introduction.md). 
        - name: participantsChoices | type: ParticipantChoices | description: Information about the booked service choices and participant count for each choice. When creating a booking, use this field only if the booking includes multiple [service variants](https://dev.wix.com/docs/rest/business-solutions/bookings/services/service-options-and-variants/introduction.md).  For example, use this for a spa package booking that includes different service levels: - 2 participants chose "Standard Package". - 1 participant chose "VIP Package". 
           - name: serviceChoices | type: array<ServiceChoices> | description: Information about the booked service choices. Includes the number of participants. 
              - name: numberOfParticipants | type: integer | description: Number of participants for this [variant](https://dev.wix.com/docs/rest/business-solutions/bookings/services/service-options-and-variants/introduction.md). 
              - name: choices | type: array<ServiceChoice> | description: Service choices for these participants. 
                 - ONE-OF: 
                    - name: custom | type: string | description: Value for one of the choices in the [`CustomServiceOption.choices`](https://example.com) list. Choices are specific values for an option the customer can choose to book. For example, the option `ageGroup` may have these choices: `child`, `student`, `adult`, and `senior`. Each choice may have a different price. 
                    - name: duration | type: Duration | description:  
                       - name: minutes | type: integer | description: Duration of the service in minutes. Min: 1 minute, Max: 30 days, 23 hours, and 59 minutes 
                       - name: name | type: string | description: Name of the duration option. Defaults to the formatted duration e.g. "1 hour, 30 minutes". 
                 - name: optionId | type: string | description: GUID of the corresponding option for the choice. For example, the choice `child` could correspond to the option `ageGroup`. In this case, `optionId` is the GUID for the `ageGroup` option. 
     - name: _id | type: string | description: Booking GUID. 
     - name: bookedEntity | type: BookedEntity | description: An object describing the bookable entity - either a specific time slot or a recurring schedule.  The structure depends on the type of service being booked:  __For appointment services__: Use `slot` to book a specific time slot with a service provider. Appointments are typically one-time sessions at a specific date and time.  __For class services__: Use `slot` to book a specific class session. Classes are individual sessions that can have multiple participants.  __For course services__: Use `schedule` to book an entire course consisting of multiple sessions over time. Courses are recurring, multi-session offerings.  Choose the appropriate field based on your service type and booking requirements. 
        - ONE-OF: - required: true
           - name: slot | type: BookedSlot | description: [Booked slot](https://dev.wix.com/docs/rest/business-solutions/bookings/bookings-and-time-slots/time-slots/availability-calendar/query-availability.md).  Specify `slot` when creating bookings for: - __Appointment-based services__: Individual sessions with service providers (consultations, treatments). Wix Bookings creates a new session when the booking is confirmed. - __Class services__: Group sessions at specific times (fitness classes, workshops). Wix Bookings links the booking to an existing scheduled session.  For course services, specify `schedule` instead of `slot`. 
              - name: serviceId | type: string | description: Service GUID. 
              - name: scheduleId | type: string | description: Schedule GUID. 
              - name: eventId | type: string | description: GUID of the corresponding [event](https://dev.wix.com/docs/rest/business-management/calendar/events-v3/introduction.md). Available for both appointment and class bookings, not available for course bookings. For appointment-based services, Wix Bookings automatically populates `eventId` when the booking `status` changes to `CONFIRMED`. For class bookings, Wix Bookings automatically populates `eventId` upon booking creation. 
              - name: startDate | type: string | description: The start time of this slot in `YYYY-MM-DDThh:mm:ss`, `YYYY-MM-DDThh:mm:ss:SSS`, or `YYYY-MM-DDThh:mm:ss:SSSZZ` [ISO-8601 format](https://en.wikipedia.org/wiki/ISO_8601). For example, `2026-01-30T13:30:00`, `2026-01-30T13:30:00:000`, or `2026-01-30T13:30:00:000-05:00`. 
              - name: endDate | type: string | description: The end time of this slot in `YYYY-MM-DDThh:mm:ss`, `YYYY-MM-DDThh:mm:ss:SSS`, or `YYYY-MM-DDThh:mm:ss:SSSZZ` [ISO-8601 format](https://en.wikipedia.org/wiki/ISO_8601). For example, `2026-01-30T13:30:00`, `2026-01-30T13:30:00:000`, or `2026-01-30T13:30:00:000-05:00`. 
              - name: timezone | type: string | description: Time zone in [IANA tz database format](https://en.wikipedia.org/wiki/Tz_database). For example, `America/New_York` or `UTC`. This is the time zone in which the slot was shown to the customer at the time of booking. Wix Bookings ensures that the slot is always displayed in this same time zone to the customer, including when they view or edit their booking in the future. 
              - name: resource | type: BookedResource | description: [Primary resource](https://dev.wix.com/docs/rest/business-solutions/bookings/resources/resources-v2/introduction.md) for the booking. For example, the [staff member](https://dev.wix.com/docs/rest/business-solutions/bookings/staff-members/introduction.md) providing the service. 
                 - name: _id | type: string | description: GUID of the booking's primary resource. 
                 - name: name | type: string | description: Resource's name at the time of booking. 
                 - name: email | type: string | description: Resource's email at the time of booking. 
                 - name: scheduleId | type: string | description: GUID of the schedule belonging to the booking's primary resource. 
              - name: location | type: Location | description: Location where the session takes place. 
                 - name: _id | type: string | description: Business location GUID. Available only for locations that are business locations, meaning the `location_type` is `"OWNER_BUSINESS"`. 
                 - name: name | type: string | description: Location name. 
                 - name: formattedAddress | type: string | description: The full address of this location. 
                 - name: formattedAddressTranslated | type: string | description: The full translated address of this location. 
                 - name: locationType | type: LocationType | description: Location type. 
                         - enum:
                         -     UNDEFINED: Undefined location type.
                         -     OWNER_BUSINESS: The business address, as set in the site’s general settings.
                         -     OWNER_CUSTOM: The address as set when creating the service.
                         -     CUSTOM: The address as set for the individual session.
              - name: resourceSelections | type: array<ResourceSelection> | description: Information about how the customer has selected resources for the booking. Each resource type may have a different selection method. Check `resource` for resource details. 
                 - name: resourceTypeId | type: string | description: GUID of the [resource type](https://dev.wix.com/docs/api-reference/business-solutions/bookings/resources/resource-types-v2/introduction.md). 
                 - name: selectionMethod | type: SelectionMethod | description: Information about how the customer has selected the resource for this resource type. 
                         - enum:
                         -     SPECIFIC_RESOURCE: The customer explicitly chose a particular resource.
                         -     ANY_RESOURCE: The customer explicitly chose "any available resource" for this resource type.
                         -     NO_SELECTION: The customer wasn't offered a resource selection or agreement option for this resource type.
           - name: schedule | type: BookedSchedule | description: [Booked schedule](https://dev.wix.com/docs/rest/business-management/calendar/schedules-v3/introduction.md).  Specify `schedule` when creating bookings for: - __Course services__: Multi-session offerings spanning weeks or months (educational courses, training programs). Wix Bookings enrolls participants in all sessions defined by the course schedule. 
              - name: scheduleId | type: string | description: [Schedule GUID](https://dev.wix.com/docs/rest/business-management/calendar/schedules-v3/introduction.md). 
              - name: serviceId | type: string | description: Booked service GUID. 
              - name: location | type: Location | description: [Location](https://dev.wix.com/docs/rest/business-management/locations/introduction.md) where the schedule's sessions take place. 
              - name: timezone | type: string | description: Time zone in [IANA tz database format](https://en.wikipedia.org/wiki/Tz_database). For example, `America/New_York` or `UTC`. This is the time zone in which the schedule was shown to the customer at the time of booking. Wix Bookings ensures that the schedule is always displayed in this same time zone to the customer, including when they view or edit their booking in the future. 
              - name: firstSessionStart | type: string | description: Start time of the first session related to the booking in `YYYY-MM-DDThh:mm:ss`, `YYYY-MM-DDThh:mm:ss:SSS`, or `YYYY-MM-DDThh:mm:ss:SSSZZ` [ISO-8601 format](https://en.wikipedia.org/wiki/ISO_8601). For example, `2026-01-30T13:30:00`, `2026-01-30T13:30:00:000`, or `2026-01-30T13:30:00:000-05:00`. 
              - name: lastSessionEnd | type: string | description: End time of the last session related to the booking in `YYYY-MM-DDThh:mm:ss`, `YYYY-MM-DDThh:mm:ss:SSS`, or `YYYY-MM-DDThh:mm:ss:SSSZZ` [ISO-8601 format](https://en.wikipedia.org/wiki/ISO_8601). For example, `2026-01-30T13:30:00`, `2026-01-30T13:30:00:000`, or `2026-01-30T13:30:00:000-05:00`. 
        - name: title | type: string | description: Session title at the time of booking. If there is no pre-existing session, for example for appointment-based services, Wix Bookings sets `title` to the service name. 
        - name: tags | type: array | description: List of tags for the booking.  - "INDIVIDUAL": For bookings of appointment-based services. Including when the appointment is for a group of participants. - "GROUP": For bookings of individual class sessions. - "COURSE": For course bookings. 
     - name: contactDetails | type: ContactDetails | description: Contact details of the site visitor or [member](https://dev.wix.com/docs/api-reference/crm/members-contacts/members/members/introduction.md) making the booking. 
        - name: contactId | type: string | description: Contact GUID. 
        - name: firstName | type: string | description: Contact's first name. When populated from a standard booking form, this property corresponds to the `name` field. 
        - name: lastName | type: string | description: Contact's last name. 
        - name: email | type: string | description: Contact's email. If no [contact](https://dev.wix.com/docs/rest/crm/members-contacts/contacts/contacts/contact-v4/contact-object.md) with this email exist, a new contact is created. Used to validate coupon usage limitations per contact. If not specified, the coupon usage limitation will not be enforced. (Coupon usage limitation validation is not supported yet). 
        - name: phone | type: string | description: Contact's phone number. 
        - name: fullAddress | type: Address | description: Contact's full address. 
           - ONE-OF: 
              - name: streetAddress | type: StreetAddress | description: Street name, number and apartment number. 
                 - name: number | type: string | description: Street number. 
                 - name: name | type: string | description: Street name. 
                 - name: apt | type: string | description: Apartment number. 
              - name: addressLine | type: string | description: Main address line, usually street and number, as free text. 
           - name: country | type: string | description: Country code. 
           - name: subdivision | type: string | description: Subdivision. Usually state, region, prefecture or province code, according to [ISO 3166-2](https://en.wikipedia.org/wiki/ISO_3166-2). 
           - name: city | type: string | description: City name. 
           - name: postalCode | type: string | description: Zip/postal code. 
           - name: addressLine2 | type: string | description: Free text providing more detailed address info. Usually contains Apt, Suite, and Floor. 
           - name: formattedAddress | type: string | description: A string containing the full address of this location. 
           - name: hint | type: string | description: Free text to help find the address. 
           - name: geocode | type: AddressLocation | description: Coordinates of the physical address. 
              - name: latitude | type: number | description: Address latitude. 
              - name: longitude | type: number | description: Address longitude. 
           - name: countryFullname | type: string | description: Country full name. 
           - name: subdivisions | type: array<Subdivision> | description: Multi-level subdivisions from top to bottom. 
              - name: code | type: string | description: Subdivision code. Usually state, region, prefecture or province code, according to [ISO 3166-2](https://en.wikipedia.org/wiki/ISO_3166-2). 
              - name: name | type: string | description: Subdivision full name. 
        - name: countryCode | type: string | description: Contact's country in [ISO 3166-1 alpha-2 code](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) format. 
     - name: status | type: BookingStatus | description: Booking status. A booking is automatically confirmed if the service allows it and an eCommerce order is created. It is automatically declined if there is a double booking and the customer hasn't paid or is eligible for an automatic refund. Currently, only payments with pricing plans are automatically refundable. 
         - enum:
         -     CREATED: The booking was created, but the customer hasn't completed the related eCommerce order yet.
         -     CONFIRMED: The merchant has confirmed the booking and it appears in the business calendar. Merchants can set up their [services](https://dev.wix.com/docs/rest/business-solutions/bookings/services/services-v2/introduction.md) to automatically confirm all `PENDING` bookings.
         -     CANCELED: The customer has canceled the booking. Depending on the relevant service's [policy snapshot](https://dev.wix.com/docs/rest/business-solutions/bookings/policies/booking-policy-snapshots/introduction.md) they may have to pay a [cancellation fee](https://dev.wix.com/docs/rest/business-solutions/bookings/pricing/booking-fees/introduction.md).
         -     PENDING: The merchant must manually confirm the booking before it appears in the business calendar.
         -     DECLINED: The merchant has declined the booking before the customer was charged.
         -     WAITING_LIST: Currently, you can't call [Register to Waitlist](https://dev.wix.com/docs/rest/business-solutions/bookings/bookings/waitlist/register-to-waitlist.md) for course or appointment bookings, even though this is supported in live sites.
     - name: paymentStatus | type: PaymentStatus | description: The payment status of the booking. This field automatically syncs with the `paymentStatus` of the corresponding [eCommerce order](https://dev.wix.com/docs/api-reference/business-solutions/e-commerce/orders/introduction.md) when customers use Wix eCommerce checkout.  ### Integration patterns  __When using Wix eCommerce checkout__: Wix Bookings automatically syncs the payment status based on the eCommerce order's payment status. Do not manually update this field.  __When using custom payment flows__: You can manually update the payment status with [Confirm Booking or Decline Booking](https://dev.wix.com/docs/api-reference/business-solutions/bookings/bookings/bookings-writer-v2/confirm-or-decline-booking.md) to reflect the customer's payment state.  __For membership/pricing plan payments__: Wix Bookings automatically manages the payment status when customers pay with an active [pricing plan](https://dev.wix.com/docs/api-reference/business-solutions/pricing-plans/pricing-plans/introduction.md) subscription.  All payment statuses are supported for every booking `status`. 
         - enum:
         -     UNDEFINED: Undefined payment status.
         -     NOT_PAID: The booking isn't paid.
         -     PAID: The booking is fully paid.
         -     PARTIALLY_PAID: The booking is partially paid.
         -     REFUNDED: The booking is refunded.
         -     EXEMPT: The booking is free of charge.
     - name: selectedPaymentOption | type: SelectedPaymentOption | description: Payment option selected by the customer. If the customer hasn't completed their checkout, they may still change the payment method. Must be one of the payment options offered by the [service](https://dev.wix.com/docs/api-reference/business-solutions/bookings/services/services-v2/introduction.md), unless `skipSelectedPaymentOptionValidation` is `true`.  When the customer pays with a [Wix eCommerce checkout](https://dev.wix.com/docs/api-reference/business-solutions/e-commerce/checkout/introduction.md), this field is required. Otherwise, the Create Booking call fails. For custom checkouts, you don't have to specify this field. 
         - enum:
         -     UNDEFINED: Undefined payment option.
         -     OFFLINE: Offline payment.
         -     ONLINE: Online payment.
         -     MEMBERSHIP: Payment using a Wix Pricing Plan.
         -     MEMBERSHIP_OFFLINE: Customers can pay only in person with a Wix Pricing Plan, while the Wix user must manually redeem the pricing plan in the dashboard.
     - name: _createdDate | type: Date | description: Date and time the booking was created in `YYYY-MM-DDThh:mm:ss.sssZ` format. 
     - name: externalUserId | type: string | description: External user GUID that you can provide. 
     - name: revision | type: string | description: Revision number to be used when updating, rescheduling, or cancelling the booking. Increments by 1 each time the booking is updated, rescheduled, or canceled. To prevent conflicting changes, the current revision must be specified when updating the booking. 
     - name: createdBy | type: IdentificationData | description: GUID of the creator of the booking. If `appId` and another GUID are present, the other GUID takes precedence. 
        - ONE-OF: 
           - name: anonymousVisitorId | type: string | description: GUID of a site visitor that has not logged in to the site. 
           - name: memberId | type: string | description: GUID of a site visitor that has logged in to the site. 
           - name: wixUserId | type: string | description: GUID of a Wix user (site owner, contributor, etc.). 
           - name: appId | type: string | description: GUID of an app. 
        - name: contactId | type: string | description: GUID of of a contact in the site's [CRM by Ascend](https://www.wix.com/ascend/crm) system. 
     - name: startDate | type: Date | description: The start date of the booking in `YYYY-MM-DDThh:mm:ss.sssZ` format. For a slot, this is the start date of the slot. For a schedule, this is the start date of the first session. 
     - name: endDate | type: Date | description: The end date of the booking in `YYYY-MM-DDThh:mm:ss.sssZ` format. For a slot, this is the end date of the slot. For a schedule, this is the end date of the last session. 
     - name: _updatedDate | type: Date | description: Date and time the booking was updated in `YYYY-MM-DDThh:mm:ss.sssZ` format. 
     - name: extendedFields | type: ExtendedFields | description: Custom field data for this object. Extended fields must be configured in the app dashboard before they can be accessed with API calls. 
        - name: namespaces | type: object | description: Extended field data. Each key corresponds to the namespace of the app that created the extended fields. The value of each key is structured according to the schema defined when the extended fields were configured.  You can only access fields for which you have the appropriate permissions.  Learn more about [extended fields](https://dev.wix.com/docs/rest/articles/getting-started/extended-fields.md). 
     - name: doubleBooked | type: boolean | description: Whether this booking overlaps with another confirmed booking. Returned only if set to `true`. 
     - name: formSubmissionId | type: string | description: GUID of the [form submission](https://dev.wix.com/docs/rest/crm/forms/form-submissions/introduction.md) associated with this booking. 
     - name: formId | type: string | description: GUID of the [form](https://dev.wix.com/docs/rest/crm/forms/form-schemas/form-object.md) associated with this booking. The value depends on how the booking was created: - For bookings created with Create Booking or Bulk Create Booking, `formId` is identical to GUID of the booking form that's associated with the relevant service. - For bookings created via Create Multi Service Booking, `formId` is set to `00000000-0000-0000-0000-000000000000` (the default booking form GUID). 
     - name: bookedAddOns | type: array<BookedAddOn> | description: List of [add-ons](https://dev.wix.com/docs/api-reference/business-solutions/bookings/services/add-ons/introduction.md) associated with the booking. 
        - name: _id | type: string | description: The GUID of the add-on. 
        - name: groupId | type: string | description: The GUID of the add-on group. 
        - name: durationInMinutes | type: integer | description: The add-on duration in minutes at the time of booking. Populated for duration-based add-ons. 
        - name: quantity | type: integer | description: The quantity of booked add-ons. For duration-based add-ons, `quantity` is not applicable. If `quantity` is provided as `1` for a duration-based add-on, it will be accepted but the value will be cleared. If any other value is provided, an `INVALID_ARGUMENT` error will be returned with the message: "Invalid AddOn details: either duration or quantity must be set correctly". 
        - name: name | type: string | description: Add-on `name` at the time of booking. 
        - name: nameTranslated | type: string | description: Add-on name translated to the language the customer used during booking. 
     - name: appId | type: string | description: GUID of the app that's associated with the booking. Inherited from the `appId` of the service associated with the booking. Bookings are displayed in Wix Bookings only if they are associated with the Wix Bookings app GUID or have no associated app GUID. For bookings from Wix apps, the following values apply: - Wix Bookings: `"13d21c63-b5ec-5912-8397-c3a5ddb27a97"` - Wix Services: `"cc552162-24a4-45e0-9695-230c4931ef40"` - Wix Meetings: `"6646a75c-2027-4f49-976c-58f3d713ed0f"` [Full list of apps created by Wix](https://dev.wix.com/docs/api-reference/articles/work-with-wix-apis/platform/about-apps-created-by-wix.md). <!-- TODO: Uncomment when Platform docs are published - Learn more about [app identity in the Bookings Platform](https://dev.wix.com/docs/api-reference/business-solutions/bookings/bookings-platform/app-identity-in-the-bookings-platform.md). --> 
     - name: createdByAppId | type: string | description: GUID of the app that created the booking. This field is used for analytics, auditing, and tracking creation sources. This read-only field is automatically populated during booking creation by checking these sources in order: 1. The caller's App GUID from the request identity context (external app or server identity). 2. The booking's `appId` field (inherited from the service's `appId`). 3. The Wix Bookings App GUID (`13d21c63-b5ec-5912-8397-c3a5ddb27a97`) as the final fallback. <!-- TODO: Uncomment when Platform docs are published - Learn more about [app identity in the Bookings Platform](https://dev.wix.com/docs/api-reference/business-solutions/bookings/bookings-platform/app-identity-in-the-bookings-platform.md). --> 
     - name: depositSelected | type: boolean | description: Whether the customer chooses to pay only the deposit amount upfront.  - `true`: The customer pays only the deposit amount upfront. - `false`: The customer pays the full price upfront.  Used only when `selectedPaymentOption` is `ONLINE` and the [service](https://dev.wix.com/docs/api-reference/business-solutions/bookings/services/services-v2/introduction.md) has a deposit amount set.  When the service supports deposit payments and `fullUpfrontPaymentAllowed` is `false`, this field must be `true`. When the service supports deposit payments and `fullUpfrontPaymentAllowed` is `true`, this field can be `true` or `false`. 

 Possible Errors:
   HTTP Code: 400 | Status Code: INVALID_ARGUMENT | Application Code: CONTACT_DETAILS_CONFLICT | Description: Contact details in the booking don't match the form submission. Ensure contactDetails and formSubmission have matching email, phone, and name values.
   HTTP Code: 400 | Status Code: INVALID_ARGUMENT | Application Code: INVALID_TIME_ZONE | Description: The time zone is invalid. Provide a valid IANA time zone identifier.
   HTTP Code: 400 | Status Code: INVALID_ARGUMENT | Application Code: INVALID_DATE_FORMAT | Description: The date format is invalid. Use the format `YYYY-MM-DDThh:mm:ss` in ISO-8601 format.
   HTTP Code: 400 | Status Code: INVALID_ARGUMENT | Application Code: INVALID_CHOICES | Description: The specified choices are invalid. Provide valid service option choices.
   HTTP Code: 403 | Status Code: PERMISSION_DENIED | Application Code: UNAUTHORIZED_OPERATION | Description: The [identity](https://dev.wix.com/docs/api-reference/articles/authentication/about-identities.md) used to call the method doesn't have the required permissions.
   HTTP Code: 403 | Status Code: PERMISSION_DENIED | Application Code: BOOKING_POLICY_VIOLATION | Description: The booking violates the service's booking policy. Check booking window restrictions, advance notice requirements, or scheduling rules.
   HTTP Code: 428 | Status Code: FAILED_PRECONDITION | Application Code: CAN_NOT_SKIP_AVAILABILITY_VALIDATION_IF_RESOURCE_NOT_PROVIDED | Description: Can't skip availability validation when no resource is provided. Specify a resource or remove the skip flag.
   HTTP Code: 428 | Status Code: FAILED_PRECONDITION | Application Code: CAN_NOT_CREATE_BOOKING_WITH_MULTI_SERVICE_BOOKING_INFO | Description: Can't create a single booking with multi-service booking information. Use the multi-service booking method instead.
   HTTP Code: 428 | Status Code: FAILED_PRECONDITION | Application Code: INVALID_FLOW_SELECTED_RESOURCES | Description: The selected resources are invalid for this booking flow. Verify the resources match the service requirements.
   HTTP Code: 428 | Status Code: FAILED_PRECONDITION | Application Code: INVALID_SERVICE_CHOICES | Description: The specified service choices are invalid. Verify the choices match the service's supported options and variants.
   HTTP Code: 428 | Status Code: FAILED_PRECONDITION | Application Code: FAILED_VALIDATING_AVAILABILITY | Description: Availability validation failed. The requested time slot or schedule may be fully booked or unavailable.
   HTTP Code: 428 | Status Code: FAILED_PRECONDITION | Application Code: SLOT_NOT_AVAILABLE | Description: The slot is no longer available for booking. It may have been booked by another customer or is outside business hours.
   HTTP Code: 428 | Status Code: FAILED_PRECONDITION | Application Code: SCHEDULE_CAPACITY_EXCEEDED | Description: The schedule capacity was exceeded. The requested number of participants exceeds available capacity.
   HTTP Code: 428 | Status Code: FAILED_PRECONDITION | Application Code: SESSION_CAPACITY_EXCEEDED | Description: The session capacity was exceeded. The requested number of participants exceeds available capacity.
   HTTP Code: 428 | Status Code: FAILED_PRECONDITION | Application Code: VALIDATION_FAILURE | Description: Validation failed. Verify all required booking fields are provided and valid.
   HTTP Code: 428 | Status Code: FAILED_PRECONDITION | Application Code: FAILED_RESOLVING_CUSTOM_CHOICES | Description: Couldn't resolve the specified service choices. Verify the choices are valid for this service.
   HTTP Code: 428 | Status Code: FAILED_PRECONDITION | Application Code: SCHEDULE_NOT_FOUND | Description: The specified schedule doesn't exist. Verify the schedule GUID is correct.
   HTTP Code: 428 | Status Code: FAILED_PRECONDITION | Application Code: SESSION_NOT_FOUND | Description: The specified session doesn't exist. Verify the session GUID is correct.


```

### Examples

### createBooking
```javascript
import { bookings } from '@wix/bookings';

async function createBooking(booking,options) {
  const response = await bookings.createBooking(booking,options);
};
```

### createBooking (with elevated permissions)
```javascript
import { bookings } from '@wix/bookings';
import { auth } from '@wix/essentials';

async function myCreateBookingMethod(booking,options) {
  const elevatedCreateBooking = auth.elevate(bookings.createBooking);
  const response = await elevatedCreateBooking(booking,options);
}
```

### createBooking (self-hosted)
Self-hosted SDK calls require you to [create a client](https://dev.wix.com/docs/sdk/articles/work-with-the-sdk/about-the-wix-client.md).

```javascript
import { createClient } from '@wix/sdk';
import { bookings } from '@wix/bookings';
// Import the auth strategy for the relevant access type
// Import the relevant host module if needed

const myWixClient = createClient ({
  modules: { bookings },
  // Include the auth strategy and host as relevant
});


async function createBooking(booking,options) {
  const response = await myWixClient.bookings.createBooking(booking,options);
};
```

---