Walk through $find

General approach is to find the slots, create the Appt resources, Post to server and present to user
Hold and Book only those of interest.
Delete, Delete Holds.

mapping of the parameters to searches


slot search parameters:

slot_sp = {
    '_id':,
    'slot-type': [],
    '_count':,  note count can be choked by server
    'schedule':,
    'schedule.actor':'',
    'start': [],
    'status':,
    'identifier':[]
    }

$find input parameters:

find_inputs ={
'start':,
'end':,
'specialty':[],
'visit-type':[],
'practitioner':[],
'organization':[],
'location-string':[],
'location-reference':[],
'patient-reference':[],
'patient-resource':[],
'coverage':[],
'reason':[]
}

mappings to slot search

'start' -->  start[] as ge[start]  slot_sp[start].append('ge'+find_inputs[start])
'end' -->  AND start[] as le[start] - doesn't work if use the same day as start  - think not implemented right on brian' server.
'specialty':[], --> PractionerRole.specialty  ( since schedule and slot lack the search parmeter  - add to the spec? - in app search!)
'visit-type':[], --> slot-type[]
'practitioner':[], --> schedule.actor=Practitioner/[id]
'organization':[], --> schedule.actor=Organization/[id]
'location-string':[], -->  need search Schedule actor:Location.address and/or actor:Practitioner.address and/or actor:Organization.address  ( need PractitionerRole to flesh out Practitioner address correctly) hold off of this for now
'location-reference':[], --> schedule.actor=Location/[id]
'patient-reference':[], --> NA  need to verify exists.
'patient-resource':[], --> NA  need to create and POST for later use and referential integrity
'coverage':[], --> NA need to create and POST for later use and referential integrity
'reason':[] --> NA need to save and use in appointment


how to do the POST stuff in Flask

1. search on Practitioner  anytime, anywhere

   - Appt links to practitioner through Slot --> Schedule --> Practitioner,  SP = schedule.actor=Practitioner/[id]

   - Create Appt based on available Slots  therefore search on Slot using a chained Schedule.actor searchset

status = free
Schedule.actor = Practitioner/arg-s-6

   e.g: `http://sqlonfhir-stu3.azurewebsites.net/fhir/Slot?status=free&schedule.actor=Practitioner/arg-s-6`

limit to three for now

   e.g: `http://sqlonfhir-stu3.azurewebsites.net/fhir/Slot?status=free&schedule.actor=Practitioner/arg-s-6&_count=3`

   slot_sp = {
       '_id':,
       'slot-type': [],
       '_count':,
       'schedule':,
       'start': [],
       'status':,
       'identifier':[]
       }

search(ref_server, rt, slot_sp)

can I generate the Appt from this?...yes!
  - need to remove empty elements or use class to construct :-?  n obvious benefit to using Class models  still need try except pattern and issues with datetime and div adn enncoding stuff in json still!  Still WIP,  doing repeats with templates a major challenge.
  - need to create unique ID  ( date + counter?  or UUID )

status =  "proposed"

serviceType - "office-visit"
specialty  -  default to GP
appointmentType  -empty ( defaults to ROUTINE )
start = slot start time
end =
participant status (2)
actor = Patient/1 (Assume easiest for simplest case)
status = "needs-action"
actor = Practitioner/arg-s-6  (from search)
status = "needs-action"
requestPeriod = 2017-09-07 ( starting on search dates )

Create these three choices and user can select from these times  -  present to user.  how does user select in flask?  possible use same html form as in index.html  with a button box and HTML 5.   ( keep it simple. )

Options: return just the appointment resources and save the Appointments locally inside Flask as a List or Post these Appointments  - The slots won't be updated.
Clear these Appointments periodically

Book/Hold - need the Id's change the slots.  For Holds release all the holds periodically.

need templates for appt, dicts?, hold and book template if able to select

need to remove empty elements or use class to construct :-?  still wind up with a lot of code systems!

assume Practitioner OR Organization  and Practitioner|Organization AND Location
todo append all practs and orgs to a single list of slots and then compare to locations. stop when find enough.



For ea Practitioner free slot look for Free Organization Slots

Exit for loop

Alt approach is to search through the actors schedules ids and find all free slots.  make appts  

slots not must supportedin appt profile  - make issue


next step is to create appts and post to server.
 load aa to server
 generalize bundler for transactions and outputs
