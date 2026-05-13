# GetAvailabilityTimeSlot

# Package: timeSlots

# Namespace: AvailabilityTimeSlots

# Method link: https://dev.wix.com/docs/api-reference/business-solutions/bookings/time-slots/time-slots-v2/get-availability-time-slot.md

## Permission Scopes:
Read Bookings Calendar Availability: SCOPE.DC-BOOKINGS.READ-CALENDAR

## Introduction

Retrieves detailed information about a specific appointment time slot.


Call this method to get complete resource availability after finding a suitable slot with [List Availability Time Slots](https://dev.wix.com/docs/api-reference/business-solutions/bookings/time-slots/time-slots-v2/list-availability-time-slots.md).

---

## REST API

### Schema

```
 Method: getAvailabilityTimeSlot
 Description: Retrieves detailed information about a specific appointment time slot.   Call this method to get complete resource availability after finding a suitable slot with [List Availability Time Slots](https://dev.wix.com/docs/api-reference/business-solutions/bookings/time-slots/time-slots-v2/list-availability-time-slots.md).  ### Defaults  Get Availability Time Slot uses the following defaults:  - Returns all available resources unless filtered by `resourceIds` or `includeResourceTypeIds`. - Includes full booking status and capacity details  ### Service type limitations  Only appointment-based services are supported when calling Get Availability Time Slot.  To retrieve class session availability, you can call [Get Event Time Slot](https://dev.wix.com/docs/api-reference/business-solutions/bookings/time-slots/time-slots-v2/get-event-time-slot.md).  To retrieve course availability, you can follow the [End-to-End Booking Flow for courses](https://dev.wix.com/docs/api-reference/business-solutions/bookings/end-to-end-booking-flows.md#book-a-course).  ### Business hours exception  Wix Bookings disregards business opening hours when all of the following conditions are met:  1. 1 or more [staff members](https://dev.wix.com/docs/api-reference/business-solutions/bookings/staff-members/staff-members/introduction.md) are needed to provide the service. 2. No other [resource type](https://dev.wix.com/docs/api-reference/business-solutions/bookings/resources/resource-types-v2/introduction.md) is needed to provide the service. 3. The service doesn't have duration-based [variants](https://dev.wix.com/docs/api-reference/business-solutions/bookings/services/service-options-and-variants/introduction.md). 4. The service doesn't support [add-ons](https://dev.wix.com/docs/api-reference/business-solutions/bookings/services/add-ons/introduction.md).  In these cases, the working hours of the relevant staff member are used instead for availability calculation.
 URL: https://www.wixapis.com/_api/service-availability/v2/time-slots/get
 Method: POST
 Required parameters: serviceId, localStartDate, localEndDate
 Method parameters: 
   param name: includeResourceTypeIds | type: array<includeResourceTypeIds> | description: IDs of the [resource types](https://dev.wix.com/docs/api-reference/business-solutions/bookings/resources/resource-types-v2/introduction.md) to check availability for. 
   param name: localEndDate | type: localEndDate | description: Local end date of the time slot in `YYYY-MM-DDThh:mm:ss` [ISO-8601 format](https://en.wikipedia.org/wiki/ISO_8601). For example, `2026-01-30T13:30:00`. | required: true
   param name: localStartDate | type: localStartDate | description: Local start date of the time slot in `YYYY-MM-DDThh:mm:ss` [ISO-8601 format](https://en.wikipedia.org/wiki/ISO_8601). For example, `2026-01-30T13:30:00`. | required: true
   param name: location | type: Location   
        - name: id | type: string | description: [Location GUID](https://dev.wix.com/docs/api-reference/business-management/locations/introduction.md). Available only for business locations. 
        - name: name | type: string | description: Location name. 
        - name: formattedAddress | type: string | description: Formatted location address. 
        - name: locationType | type: LocationType | description: Location type. 
             - enum:
             -     BUSINESS: A business location, either the default business address, or locations defined for the business by the Business Info.
             -     CUSTOM: The location is unique to this service and isn't defined as 1 of the business locations.
             -     CUSTOMER: The location can be determined by the customer and isn't set up beforehand.
   param name: resourceTypes | type: array<resourceTypes> | description: Resource types to filter time slots. Only returns time slots that have these specific resource types available. This filters the time slots themselves, unlike `includeResourceTypeIds` which only controls response details. 
              - name: resourceTypeId | type: string | description: [Resource type GUID](https://dev.wix.com/docs/api-reference/business-solutions/bookings/resources/resource-types-v2/introduction.md). 
              - name: resourceIds | type: array | description: Resource GUIDs. Available only if there is at least 1 resource available for the slot. 
   param name: serviceId | type: serviceId | description: Service GUID of the time slot. You must specify the GUID of an appointment-based service. | required: true
   param name: timeZone | type: timeZone | description: Time zone in [IANA tz database format](https://en.wikipedia.org/wiki/Tz_database) for adjusting `fromLocalDate` and `toLocalDate`. For example, `America/New_York` or `UTC`.  Default: `timeZone` specified in the business [site properties](https://dev.wix.com/docs/api-reference/business-management/site-properties/properties/get-site-properties.md). 
 Return type: GetAvailabilityTimeSlotResponse
  - name: timeSlot | type: TimeSlot | description: Retrieved time slot. 
     - name: serviceId | type: string | description: [Service GUID] (https://dev.wix.com/docs/api-reference/business-solutions/bookings/services/services-v2/introduction.md).  Available only for single-service bookings. For multi-service bookings, this field is empty and individual service GUIDs are provided in `nestedTimeSlots`. 
     - name: localStartDate | type: string | description: Local start date of the time slot in `YYYY-MM-DDThh:mm:ss` [ISO-8601 format](https://en.wikipedia.org/wiki/ISO_8601). For example, `2026-01-30T13:30:00`.  For multi-service bookings, this represents the start time of the first service in the sequence. 
     - name: localEndDate | type: string | description: Local end date of the time slot in `YYYY-MM-DDThh:mm:ss` [ISO-8601 format](https://en.wikipedia.org/wiki/ISO_8601). For example, `2026-01-30T14:00:00`.  For multi-service bookings, this represents the end time of the last service in the sequence. 
     - name: bookable | type: boolean | description: Whether customers can book the slot according to the service's [booking policies](https://dev.wix.com/docs/api-reference/business-solutions/bookings/policies/booking-policies/introduction.md).  For multi-service bookings, this is `true` only when all services in the sequence comply with their respective booking policies. 
     - name: location | type: Location | description: Information about where the business provides the service to the customer. 
        - name: id | type: string | description: [Location GUID](https://dev.wix.com/docs/api-reference/business-management/locations/introduction.md). Available only for business locations. 
        - name: name | type: string | description: Location name. 
        - name: formattedAddress | type: string | description: Formatted location address. 
        - name: locationType | type: LocationType | description: Location type. 
             - enum:
             -     BUSINESS: A business location, either the default business address, or locations defined for the business by the Business Info.
             -     CUSTOM: The location is unique to this service and isn't defined as 1 of the business locations.
             -     CUSTOMER: The location can be determined by the customer and isn't set up beforehand.
     - name: eventInfo | type: EventInfo | description: Information about the [event](https://dev.wix.com/docs/api-reference/business-management/calendar/events-v3/introduction.md) related to the slot. Available only for classes. Not available for appointment-based services and courses. 
        - name: eventId | type: string | description: Event GUID. 
        - name: waitingList | type: WaitingList | description: Information about the event's waitlist. Available only if the service has a waitlist. 
           - name: totalCapacity | type: integer | description: Total number of spots in the waitlist. 
           - name: remainingCapacity | type: integer | description: Number of remaining spots in the waitlist. For example, an event with a waitlist for 10 people and 3 registrants, results in a remaining capacity of `7`. 
        - name: eventTitle | type: string | description: Event title. 
     - name: totalCapacity | type: integer | description: Total number of spots for the slot.  For multi-service bookings, this is always `1` because customers book the entire service sequence as a single unit. 
     - name: remainingCapacity | type: integer | description: Remaining number of spots for the slot. - For appointment bookings: Either `1` (available) or `0` (unavailable). - For classes: Total capacity minus booked spots. Doesn't account for waitlist reservations. For classes with waitlists, use `bookableCapacity` to get the actual number of spots customers can book. - For courses: Total capacity minus booked spots. Courses don't currently support waitlists. 
     - name: bookableCapacity | type: integer | description: Number of spots that customers can book for the slot. Calculated as the remaining capacity minus the spots reserved for the waitlist. If the service has no waitlist, identical to `remainingCapacity`.  For multi-service bookings, this is either `1` (sequence can be booked) or `0` (sequence can't be booked). 
     - name: bookingPolicyViolations | type: BookingPolicyViolations | description: Information about booking policy violations for the slot.  For multi-service bookings, this aggregates violations from all services in the sequence. 
        - name: tooEarlyToBook | type: boolean | description: Whether it's too early for customers to book the slot.  By default, all slots are returned. Specifying `{"tooEarlyToBook": false}` returns only those that customers can already book, while specifying `{"tooEarlyToBook": true}` returns only those that can't be booked yet. 
        - name: earliestBookingDate | type: string | description: Earliest time for booking the slot in `YYYY-MM-DDThh:mm:ss.sssZ` format.  *In responses**: Contains a value when `tooEarlyToBook` is `true`, indicating the earliest time customers can book the slot.  *In requests**: Don't specify a value for this field. Use `tooEarlyToBook` to filter slots that can't be booked yet due to minimum advance booking time restrictions. 
        - name: tooLateToBook | type: boolean | description: Whether it's too late for customers to book the slot.  By default, all slots are returned. Specifying `{"tooLateToBook": false}` returns only those that customers can still book, while specifying `{"tooLateToBook": true}` returns only those that can no longer be booked. 
        - name: bookOnlineDisabled | type: boolean | description: Whether customers can book the service online.  By default, both services with online booking enabled and disabled are returned. Providing the boolean set to `true` or `false` returns only matching slots. 
     - name: availableResources | type: array<AvailableResources> | description: List of [resources](https://dev.wix.com/docs/api-reference/business-solutions/bookings/resources/resources-v2/introduction.md) available during the time slot.  Available only for single-service bookings. For multi-service bookings, resource information is provided in `nestedTimeSlots`.  __Note__: For [List Availability Time Slots](https://dev.wix.com/docs/api-reference/business-solutions/bookings/time-slots/time-slots-v2/list-availability-time-slots.md), this list is empty by default. To include resource details, specify `includeResourceTypeIds` or `resourceIds` in the request. For [Get Availability Time Slot](https://dev.wix.com/docs/api-reference/business-solutions/bookings/time-slots/time-slots-v2/get-availability-time-slot.md), all resources are returned by default. 
        - name: resourceTypeId | type: string | description: [Resource type GUID](https://dev.wix.com/docs/api-reference/business-solutions/bookings/resources/resource-types-v2/introduction.md). 
        - name: resources | type: array<Resource> | description: Details about resources available during the time slot.  Behavior varies by method:  List methods (List Availability Time Slots and List Multi Service Availability Time Slots): - Empty by default. - Up to 10 resources when specifying `includeResourceTypeIds` or `resourceIds` in the request.  Get methods (Get Availability Time Slots and Get Multi Service Availability Time Slots): - All resources by default. - Filtered resources when specifying `includeResourceTypeIds` or `resourceIds` in the request. 
           - name: id | type: string | description: Resource GUID. 
           - name: name | type: string | description: Resource name. 
        - name: hasMoreAvailableResources | type: boolean | description: Whether there are more available resources for the slot than those listed in `resources`. 
     - name: nestedTimeSlots | type: array<NestedTimeSlot> | description: Nested time slots for multi-service bookings. Each nested slot represents 1 service in the sequence, ordered according to the service sequence specified in the request.  Available only for multi-service bookings. Empty for single-service bookings. 
        - name: serviceId | type: string | description: Service GUID of the nested time slot. 
        - name: localStartDate | type: string | description: Local start date of the nested time slot in `YYYY-MM-DDThh:mm:ss` [ISO-8601 format](https://en.wikipedia.org/wiki/ISO_8601). For example, `2026-01-30T13:30:00`. 
        - name: localEndDate | type: string | description: Local end date of the nested time slot in `YYYY-MM-DDThh:mm:ss` [ISO-8601 format](https://en.wikipedia.org/wiki/ISO_8601). For example, `2026-01-30T13:30:00`. 
        - name: availableResources | type: array<AvailableResources> | description: List of [resources](https://dev.wix.com/docs/api-reference/business-solutions/bookings/resources/resources-v2/introduction.md) available during the nested time slot. 
        - name: scheduleId | type: string | description: The schedule GUID associated with this nested time slot. Same as the service's schedule GUID. 
     - name: nonBookableReasons | type: NonBookableReasons | description: Information about why customers can't book the time slot. 
        - name: noRemainingCapacity | type: boolean | description: Whether the slot is fully booked with no remaining capacity. 
        - name: violatesBookingPolicy | type: boolean | description: Whether booking the slot violates any of the service's booking policies. 
        - name: reservedForWaitingList | type: boolean | description: Whether the slot is reserved for the waitlist. A new customer can't book the reserved slot. 
        - name: eventCancelled | type: boolean | description: Whether the related event is cancelled. 
     - name: scheduleId | type: string | description: Schedule GUID associated with this time slot. Same as the service's schedule GUID. 
  - name: timeZone | type: string | description: Time zone in [IANA tz database format](https://en.wikipedia.org/wiki/Tz_database) for adjusting `fromLocalDate` and `toLocalDate`. For example, `America/New_York` or `UTC`.  Default: `timeZone` specified in the business [site properties](https://dev.wix.com/docs/api-reference/business-management/site-properties/properties/get-site-properties.md). 

 Possible Errors:
   HTTP Code: 403 | Status Code: PERMISSION_DENIED | Application Code: UNAUTHORIZED_OPERATION | Description: The [identity](https://dev.wix.com/docs/api-reference/articles/authentication/about-identities.md) used to call the method doesn't have the required permissions.
   HTTP Code: 404 | Status Code: NOT_FOUND | Application Code: MULTIPLE_IMPLEMENTERS_FOUND | Description: Multiple availability providers are installed. Only 1 provider can be active at a time.
   HTTP Code: 404 | Status Code: NOT_FOUND | Application Code: NO_IMPLEMENTERS_FOUND | Description: No availability provider is installed or configured for this operation.
   HTTP Code: 404 | Status Code: NOT_FOUND | Application Code: SLOT_NOT_FOUND | Description: Couldn't find a time slot matching the specified criteria.


```

### Examples

### Check availability with specific staff preference
Verifies appointment availability when requesting specific healthcare providers, returning which of the requested doctors are available for the time slot.

```curl
curl -X POST 'https://www.wixapis.com/_api/service-availability/v2/time-slots/get' \
-H 'Authorization: <AUTH>' \
-d '{
   "resourceTypes": [
      {
         "resourceTypeId": "1cd44cf8-756f-41c3-bd90-3e2ffcaf1155",
         "resourceIds": [
            "167b22cd-0521-47b9-b0c2-baca665351c5",
            "b44e0801-223e-4124-bcbc-0eb4c07cba13",
            "fd01e7c0-4ffc-42c3-9f7b-73b46c9e1664",
            "627d45ed-71bd-4f6c-b90f-fc5b037accc6",
            "1bd089a1-726b-4fdd-9a70-4b19cffeb392",
            "510fc9f3-f291-4155-a3dc-cb96ae06f14f"
         ]
      }
   ],
   "location":{
      "id": "b4698671-3412-49b5-bff1-f50d4d0fe3b3",
      "locationType": "BUSINESS"
   },
   "serviceId": "27f2fb02-8925-4ede-be26-991411d6c905",
   "localStartDate": "2025-09-15T14:00:00",
   "localEndDate": "2025-09-15T15:00:00",
   "timeZone": "America/New_York"
}'
```

### Check specific appointment slot availability
Verifies availability for a specific appointment time slot and returns which healthcare providers are available to deliver the service.

```curl
curl -X POST 'https://www.wixapis.com/_api/service-availability/v2/time-slots/get' \
-H 'Authorization: <AUTH>' \
-d '{
    "serviceId": "27f2fb02-8925-4ede-be26-991411d6c905",
    "location":
      {
        "id": "b4698671-3412-49b5-bff1-f50d4d0fe3b3",
        "locationType": "BUSINESS"
      },
    "localStartDate": "2025-09-15T14:00:00",
    "localEndDate": "2025-09-15T15:00:00",
    "timeZone": "America/New_York"
}'
```

---

## JavaScript SDK

### Schema

```
 Method: wixClientAdmin.timeSlots.AvailabilityTimeSlots.getAvailabilityTimeSlot(serviceId, localStartDate, localEndDate, timeZone, location, options)
 Description: Retrieves detailed information about a specific appointment time slot.   Call this method to get complete resource availability after finding a suitable slot with [List Availability Time Slots](https://dev.wix.com/docs/api-reference/business-solutions/bookings/time-slots/time-slots-v2/list-availability-time-slots.md).  ### Defaults  Get Availability Time Slot uses the following defaults:  - Returns all available resources unless filtered by `resourceIds` or `includeResourceTypeIds`. - Includes full booking status and capacity details  ### Service type limitations  Only appointment-based services are supported when calling Get Availability Time Slot.  To retrieve class session availability, you can call [Get Event Time Slot](https://dev.wix.com/docs/api-reference/business-solutions/bookings/time-slots/time-slots-v2/get-event-time-slot.md).  To retrieve course availability, you can follow the [End-to-End Booking Flow for courses](https://dev.wix.com/docs/api-reference/business-solutions/bookings/end-to-end-booking-flows.md#book-a-course).  ### Business hours exception  Wix Bookings disregards business opening hours when all of the following conditions are met:  1. 1 or more [staff members](https://dev.wix.com/docs/api-reference/business-solutions/bookings/staff-members/staff-members/introduction.md) are needed to provide the service. 2. No other [resource type](https://dev.wix.com/docs/api-reference/business-solutions/bookings/resources/resource-types-v2/introduction.md) is needed to provide the service. 3. The service doesn't have duration-based [variants](https://dev.wix.com/docs/api-reference/business-solutions/bookings/services/service-options-and-variants/introduction.md). 4. The service doesn't support [add-ons](https://dev.wix.com/docs/api-reference/business-solutions/bookings/services/add-ons/introduction.md).  In these cases, the working hours of the relevant staff member are used instead for availability calculation.
 Required parameters: serviceId, localStartDate, localEndDate, timeZone, location
 Method parameters: 
   param name: localEndDate | type: string | description: Local end date of the time slot in `YYYY-MM-DDThh:mm:ss` [ISO-8601 format](https://en.wikipedia.org/wiki/ISO_8601). For example, `2026-01-30T13:30:00`. | required: true
   param name: localStartDate | type: string | description: Local start date of the time slot in `YYYY-MM-DDThh:mm:ss` [ISO-8601 format](https://en.wikipedia.org/wiki/ISO_8601). For example, `2026-01-30T13:30:00`. | required: true
   param name: location | type: Location   | required: true
        - name: _id | type: string | description: [Location GUID](https://dev.wix.com/docs/api-reference/business-management/locations/introduction.md). Available only for business locations. 
        - name: name | type: string | description: Location name. 
        - name: formattedAddress | type: string | description: Formatted location address. 
        - name: locationType | type: LocationType | description: Location type. 
             - enum:
             -     BUSINESS: A business location, either the default business address, or locations defined for the business by the Business Info.
             -     CUSTOM: The location is unique to this service and isn't defined as 1 of the business locations.
             -     CUSTOMER: The location can be determined by the customer and isn't set up beforehand.
   param name: options | type: GetAvailabilityTimeSlotOptions  none 
        - name: includeResourceTypeIds | type: array | description: IDs of the [resource types](https://dev.wix.com/docs/api-reference/business-solutions/bookings/resources/resource-types-v2/introduction.md) to check availability for. 
        - name: resourceTypes | type: array<ResourceType> | description: Resource types to filter time slots. Only returns time slots that have these specific resource types available. This filters the time slots themselves, unlike `includeResourceTypeIds` which only controls response details. 
           - name: resourceTypeId | type: string | description: [Resource type GUID](https://dev.wix.com/docs/api-reference/business-solutions/bookings/resources/resource-types-v2/introduction.md). 
           - name: resourceIds | type: array | description: Resource GUIDs. Available only if there is at least 1 resource available for the slot. 
   param name: serviceId | type: string | description: Service GUID of the time slot. You must specify the GUID of an appointment-based service. | required: true
   param name: timeZone | type: string | description: Time zone in [IANA tz database format](https://en.wikipedia.org/wiki/Tz_database) for adjusting `fromLocalDate` and `toLocalDate`. For example, `America/New_York` or `UTC`.  Default: `timeZone` specified in the business [site properties](https://dev.wix.com/docs/api-reference/business-management/site-properties/properties/get-site-properties.md). | required: true
 Return type: PROMISE<GetAvailabilityTimeSlotResponse>
  - name: timeSlot | type: TimeSlot | description: Retrieved time slot. 
     - name: serviceId | type: string | description: [Service GUID] (https://dev.wix.com/docs/api-reference/business-solutions/bookings/services/services-v2/introduction.md).  Available only for single-service bookings. For multi-service bookings, this field is empty and individual service GUIDs are provided in `nestedTimeSlots`. 
     - name: localStartDate | type: string | description: Local start date of the time slot in `YYYY-MM-DDThh:mm:ss` [ISO-8601 format](https://en.wikipedia.org/wiki/ISO_8601). For example, `2026-01-30T13:30:00`.  For multi-service bookings, this represents the start time of the first service in the sequence. 
     - name: localEndDate | type: string | description: Local end date of the time slot in `YYYY-MM-DDThh:mm:ss` [ISO-8601 format](https://en.wikipedia.org/wiki/ISO_8601). For example, `2026-01-30T14:00:00`.  For multi-service bookings, this represents the end time of the last service in the sequence. 
     - name: bookable | type: boolean | description: Whether customers can book the slot according to the service's [booking policies](https://dev.wix.com/docs/api-reference/business-solutions/bookings/policies/booking-policies/introduction.md).  For multi-service bookings, this is `true` only when all services in the sequence comply with their respective booking policies. 
     - name: location | type: Location | description: Information about where the business provides the service to the customer. 
        - name: _id | type: string | description: [Location GUID](https://dev.wix.com/docs/api-reference/business-management/locations/introduction.md). Available only for business locations. 
        - name: name | type: string | description: Location name. 
        - name: formattedAddress | type: string | description: Formatted location address. 
        - name: locationType | type: LocationType | description: Location type. 
             - enum:
             -     BUSINESS: A business location, either the default business address, or locations defined for the business by the Business Info.
             -     CUSTOM: The location is unique to this service and isn't defined as 1 of the business locations.
             -     CUSTOMER: The location can be determined by the customer and isn't set up beforehand.
     - name: eventInfo | type: EventInfo | description: Information about the [event](https://dev.wix.com/docs/api-reference/business-management/calendar/events-v3/introduction.md) related to the slot. Available only for classes. Not available for appointment-based services and courses. 
        - name: eventId | type: string | description: Event GUID. 
        - name: waitingList | type: WaitingList | description: Information about the event's waitlist. Available only if the service has a waitlist. 
           - name: totalCapacity | type: integer | description: Total number of spots in the waitlist. 
           - name: remainingCapacity | type: integer | description: Number of remaining spots in the waitlist. For example, an event with a waitlist for 10 people and 3 registrants, results in a remaining capacity of `7`. 
        - name: eventTitle | type: string | description: Event title. 
     - name: totalCapacity | type: integer | description: Total number of spots for the slot.  For multi-service bookings, this is always `1` because customers book the entire service sequence as a single unit. 
     - name: remainingCapacity | type: integer | description: Remaining number of spots for the slot. - For appointment bookings: Either `1` (available) or `0` (unavailable). - For classes: Total capacity minus booked spots. Doesn't account for waitlist reservations. For classes with waitlists, use `bookableCapacity` to get the actual number of spots customers can book. - For courses: Total capacity minus booked spots. Courses don't currently support waitlists. 
     - name: bookableCapacity | type: integer | description: Number of spots that customers can book for the slot. Calculated as the remaining capacity minus the spots reserved for the waitlist. If the service has no waitlist, identical to `remainingCapacity`.  For multi-service bookings, this is either `1` (sequence can be booked) or `0` (sequence can't be booked). 
     - name: bookingPolicyViolations | type: BookingPolicyViolations | description: Information about booking policy violations for the slot.  For multi-service bookings, this aggregates violations from all services in the sequence. 
        - name: tooEarlyToBook | type: boolean | description: Whether it's too early for customers to book the slot.  By default, all slots are returned. Specifying `{"tooEarlyToBook": false}` returns only those that customers can already book, while specifying `{"tooEarlyToBook": true}` returns only those that can't be booked yet. 
        - name: earliestBookingDate | type: Date | description: Earliest time for booking the slot in `YYYY-MM-DDThh:mm:ss.sssZ` format.  *In responses**: Contains a value when `tooEarlyToBook` is `true`, indicating the earliest time customers can book the slot.  *In requests**: Don't specify a value for this field. Use `tooEarlyToBook` to filter slots that can't be booked yet due to minimum advance booking time restrictions. 
        - name: tooLateToBook | type: boolean | description: Whether it's too late for customers to book the slot.  By default, all slots are returned. Specifying `{"tooLateToBook": false}` returns only those that customers can still book, while specifying `{"tooLateToBook": true}` returns only those that can no longer be booked. 
        - name: bookOnlineDisabled | type: boolean | description: Whether customers can book the service online.  By default, both services with online booking enabled and disabled are returned. Providing the boolean set to `true` or `false` returns only matching slots. 
     - name: availableResources | type: array<AvailableResources> | description: List of [resources](https://dev.wix.com/docs/api-reference/business-solutions/bookings/resources/resources-v2/introduction.md) available during the time slot.  Available only for single-service bookings. For multi-service bookings, resource information is provided in `nestedTimeSlots`.  __Note__: For [List Availability Time Slots](https://dev.wix.com/docs/api-reference/business-solutions/bookings/time-slots/time-slots-v2/list-availability-time-slots.md), this list is empty by default. To include resource details, specify `includeResourceTypeIds` or `resourceIds` in the request. For [Get Availability Time Slot](https://dev.wix.com/docs/api-reference/business-solutions/bookings/time-slots/time-slots-v2/get-availability-time-slot.md), all resources are returned by default. 
        - name: resourceTypeId | type: string | description: [Resource type GUID](https://dev.wix.com/docs/api-reference/business-solutions/bookings/resources/resource-types-v2/introduction.md). 
        - name: resources | type: array<Resource> | description: Details about resources available during the time slot.  Behavior varies by method:  List methods (List Availability Time Slots and List Multi Service Availability Time Slots): - Empty by default. - Up to 10 resources when specifying `includeResourceTypeIds` or `resourceIds` in the request.  Get methods (Get Availability Time Slots and Get Multi Service Availability Time Slots): - All resources by default. - Filtered resources when specifying `includeResourceTypeIds` or `resourceIds` in the request. 
           - name: _id | type: string | description: Resource GUID. 
           - name: name | type: string | description: Resource name. 
        - name: hasMoreAvailableResources | type: boolean | description: Whether there are more available resources for the slot than those listed in `resources`. 
     - name: nestedTimeSlots | type: array<NestedTimeSlot> | description: Nested time slots for multi-service bookings. Each nested slot represents 1 service in the sequence, ordered according to the service sequence specified in the request.  Available only for multi-service bookings. Empty for single-service bookings. 
        - name: serviceId | type: string | description: Service GUID of the nested time slot. 
        - name: localStartDate | type: string | description: Local start date of the nested time slot in `YYYY-MM-DDThh:mm:ss` [ISO-8601 format](https://en.wikipedia.org/wiki/ISO_8601). For example, `2026-01-30T13:30:00`. 
        - name: localEndDate | type: string | description: Local end date of the nested time slot in `YYYY-MM-DDThh:mm:ss` [ISO-8601 format](https://en.wikipedia.org/wiki/ISO_8601). For example, `2026-01-30T13:30:00`. 
        - name: availableResources | type: array<AvailableResources> | description: List of [resources](https://dev.wix.com/docs/api-reference/business-solutions/bookings/resources/resources-v2/introduction.md) available during the nested time slot. 
        - name: scheduleId | type: string | description: The schedule GUID associated with this nested time slot. Same as the service's schedule GUID. 
     - name: nonBookableReasons | type: NonBookableReasons | description: Information about why customers can't book the time slot. 
        - name: noRemainingCapacity | type: boolean | description: Whether the slot is fully booked with no remaining capacity. 
        - name: violatesBookingPolicy | type: boolean | description: Whether booking the slot violates any of the service's booking policies. 
        - name: reservedForWaitingList | type: boolean | description: Whether the slot is reserved for the waitlist. A new customer can't book the reserved slot. 
        - name: eventCancelled | type: boolean | description: Whether the related event is cancelled. 
     - name: scheduleId | type: string | description: Schedule GUID associated with this time slot. Same as the service's schedule GUID. 
  - name: timeZone | type: string | description: Time zone in [IANA tz database format](https://en.wikipedia.org/wiki/Tz_database) for adjusting `fromLocalDate` and `toLocalDate`. For example, `America/New_York` or `UTC`.  Default: `timeZone` specified in the business [site properties](https://dev.wix.com/docs/api-reference/business-management/site-properties/properties/get-site-properties.md). 

 Possible Errors:
   HTTP Code: 403 | Status Code: PERMISSION_DENIED | Application Code: UNAUTHORIZED_OPERATION | Description: The [identity](https://dev.wix.com/docs/api-reference/articles/authentication/about-identities.md) used to call the method doesn't have the required permissions.
   HTTP Code: 404 | Status Code: NOT_FOUND | Application Code: MULTIPLE_IMPLEMENTERS_FOUND | Description: Multiple availability providers are installed. Only 1 provider can be active at a time.
   HTTP Code: 404 | Status Code: NOT_FOUND | Application Code: NO_IMPLEMENTERS_FOUND | Description: No availability provider is installed or configured for this operation.
   HTTP Code: 404 | Status Code: NOT_FOUND | Application Code: SLOT_NOT_FOUND | Description: Couldn't find a time slot matching the specified criteria.


```

### Examples

### getAvailabilityTimeSlot
```javascript
import { availabilityTimeSlots } from '@wix/bookings';

async function getAvailabilityTimeSlot(serviceId,localStartDate,localEndDate,timeZone,location,options) {
  const response = await availabilityTimeSlots.getAvailabilityTimeSlot(serviceId,localStartDate,localEndDate,timeZone,location,options);
};
```

### getAvailabilityTimeSlot (with elevated permissions)
```javascript
import { availabilityTimeSlots } from '@wix/bookings';
import { auth } from '@wix/essentials';

async function myGetAvailabilityTimeSlotMethod(serviceId,localStartDate,localEndDate,timeZone,location,options) {
  const elevatedGetAvailabilityTimeSlot = auth.elevate(availabilityTimeSlots.getAvailabilityTimeSlot);
  const response = await elevatedGetAvailabilityTimeSlot(serviceId,localStartDate,localEndDate,timeZone,location,options);
}
```

### getAvailabilityTimeSlot (self-hosted)
Self-hosted SDK calls require you to [create a client](https://dev.wix.com/docs/sdk/articles/work-with-the-sdk/about-the-wix-client.md).

```javascript
import { createClient } from '@wix/sdk';
import { availabilityTimeSlots } from '@wix/bookings';
// Import the auth strategy for the relevant access type
// Import the relevant host module if needed

const myWixClient = createClient ({
  modules: { availabilityTimeSlots },
  // Include the auth strategy and host as relevant
});


async function getAvailabilityTimeSlot(serviceId,localStartDate,localEndDate,timeZone,location,options) {
  const response = await myWixClient.availabilityTimeSlots.getAvailabilityTimeSlot(serviceId,localStartDate,localEndDate,timeZone,location,options);
};
```

---