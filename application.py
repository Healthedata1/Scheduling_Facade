#! /usr/bin/env python3.4
# run in venv 3.4 same as AWS EB
from flask import Flask, request, render_template, jsonify
import requests
import json
import datetime
import fhirtemplates as f

import fhirclient.models.appointment as Appt
import fhirclient.models.bundle as Bundle
import fhirclient.models.slot as Slot
import fhirclient.models.operationoutcome as OO
import fhirclient.models.fhirreference as FRef
import fhirclient.models.fhirdate as FDate
import fhirclient.models.period as Period
import fhirclient.models.codeableconcept as CC
import fhirclient.models.coding as Coding

import logging
#logging.disable(logging.CRITICAL)
logging.basicConfig(filename='myProgram.log',level=logging.DEBUG, format=' %(asctime)s - %(levelname)s- %(message)s')
logging.debug('Start of program')
logging.info('The logging module is working.')

ref_server = 'http://sqlonfhir-stu3.azurewebsites.net/fhir'
count = 100
def slot_sp_convert(op, actor = None):  # the actor is pract[i]|org[i]|location[i] based on nested loop and OR ing
    slot_sp = {
        'slot-type': [],
        'schedule.actor': None,
        'start': [],
        'status': 'free', # fixed for now
        '_count': count  # fix to 3 for testing
        }

    try:  # visit-types
        slot_sp['slot-type'] = [k for k in op['visit-type']]
    except KeyError:
        pass

    slot_sp['schedule.actor'] = actor

    try:  # date params for slot and schedule
        slot_sp['start'] = ['ge' + k for k in op['start']]
    except KeyError:
        pass

    try:  # date params for slot and schedule
        slot_sp['start'] = slot_sp['start'] + ['le' + k for k in op['end']]
    except KeyError:
        pass

    try:  # may get rid of this and apply at the end.
        slot_sp['_count'] = op['_count']
    except KeyError:
        pass

    return(slot_sp)


def search(ref_server, res_type, sp={}):
    res_id = []
    url = '{}/{}'.format(ref_server, res_type)
    headers = {'Content-Type': 'application/fhir+json', 'Accept': 'application/fhir+json'}
    r = requests.get(url, headers=headers, params=sp)
    # Return server response ...
    try:
        res_id = [i['resource']['id'] for i in r.json()['entry']]
    except KeyError:
        pass
    except ValueError:  # includes simplejson.decoder.JSONDecodeError
        pass
    try:
        res_narr = [i['resource']['text']['div'] for i in r.json()['entry']]
    except KeyError:
        pass
    except ValueError:  # includes simplejson.decoder.JSONDecodeError
        pass
    try:
        return(r.status_code, r.reason, r.headers, r.json(), res_id, res_narr) # return a tuple access with usual operations
    except:
        return(r.status_code, r.reason, r.headers, {}, None, None)  # return a tuple access with usual operations  note the json.dumps(dict(r.headers)) make case insensitive dict makes possible to dump


def timestamp():
    # get url freindly time stamp
    dts = str(datetime.datetime.utcnow().isoformat())
    dts = dts.replace(':', '')
    dts = dts.replace('.', '')
    return(dts)


def get_slots(op, actor=None):
    slot_sp = slot_sp_convert(op, actor)  # dict of search params converted to FHIR search param for slot
    res_json = search(ref_server, 'Slot', slot_sp)[3]
    # unbundle res from search results and add to the slot list
    bundle = Bundle.Bundle(res_json)
    slots = [be.resource for be in bundle.entry] if bundle is not None and bundle.entry is not None else None
    # logging.info('slots[0] is: {}'.format(slots[0].as_json()))
    return(slots)




def map_cc(concept):
    # create CodeableConcept based on slot data
    cc = CC.CodeableConcept()
    cc.coding = []
    cc.text = concept.text
    try:
        cc_coding = Coding.Coding()
        for translation in concept.coding:
            cc_coding.code = translation.code
            cc_coding.display = translation.display
            cc_coding.system = translation.system
            cc.coding.append(cc_coding)
    except TypeError:  # coding missing
        pass
    return(cc)

def map_part(url):
    part = Appt.AppointmentParticipant()
    part.actor = FRef.FHIRReference({'reference': url})
    part.status = 'needs-action'
    return(part)


def make_appts(op, slot=None):
    # create Appt based on slot data
    logging.info('slot as json = {}',format(json.dumps(slot.as_json(),sort_keys=True, indent=4)))
    appt = Appt.Appointment()
    appt.id = '{}{}'.format(timestamp(), slot.id)
    appt.status = 'pending'
    try: #  mapping serviceType
        appt.serviceType = []  # codeable pattern
        for concept in slot.serviceType:
            appt.serviceType.append(map_cc(concept))
    except TypeError:  # element missing
        pass
    try: #  mapping specialty
        appt.specialty = []  # codeable pattern
        for concept in slot.specialty:  # only the first translation for now
            appt.specialty.append(map_cc(concept))
    except TypeError:  # element missing
        pass
    #  mapping appointmetType
    try:
        concept = slot.appointmentType
        appt.appointmentType = map_cc(concept)
    except AttributeError:  # element missing
        pass
    try:
        appt.reason=[]
        for concept in op['reason']:
            # create CodeableConcept based on op data - just text for now
            appt.reason.append = (CC.CodeableConcept({'text': concept}))
    except KeyError:  # op missing
        pass

    appt.start = slot.start
    appt.end = slot.end
    appt.slot =[FRef.FHIRReference({'reference': 'Slot/{}'.format(slot.id)})]  # option a

    appt.participant = []
    '''
    assume a list of participant references from op
    'practitioner':[],
    'organization':[],
    'location-reference':[],
    'patient-reference':[],
    'patient-resource':[], do this one later...
    '''
    try:
        for url in op['practitioner']:
            logging.info('practitioner is = {}'.format(op))
            appt.participant.append(map_part(url))
    except KeyError:
        pass
    try:
        for url in op['organization']:
            appt.participant.append(map_part(url))
    except KeyError:
        pass
    try:
        for url in op['location-reference']:
            appt.participant.append(map_part(url))
    except KeyError:
        pass
    try:
        for url in op['patient-reference']:
            appt.participant.append(map_part(url))
    except KeyError:
        pass
    #  mapping  this comes from the query parameter to requested period there is only one and is required
    pd = Period.Period()
    fd = FDate.FHIRDate()
    try:
        fd.origval = op['start']  # start sp
        pd.start = fd
    except KeyError:
        fd.origval = '2017-09-07'  # start sp
        pd.start = fd
    try:
        fd.origval = op['end']  # end sp
        pd.end = fd
    except KeyError:
        pass
    appt.requestedPeriod = []
    appt.requestedPeriod.append(pd)
    return(appt)


def aa_bundler(appts):  # make the operation output bundle
    new_bundle = Bundle.Bundle()
    new_bundle.id = '{}-argo-aab'.format(timestamp())
    new_bundle.type = 'searchset'
    new_bundle.total = len(appts)  # need to keep count same a op parameter
    new_bundle.entry = []
    for res in appts:  #  or appts assume a list of resources
        entry = Bundle.BundleEntry()
        entry.fullUrl = '{}/{}/{}'.format(ref_server, res.resource_type, res.id)
        entry.resource = res
        entry.search = Bundle.BundleEntrySearch({'mode':'match'})
        new_bundle.entry.append(entry)
    # OO stubbed in here:
    entry = Bundle.BundleEntry()
    entry.fullUrl = '{}/{}/{}'.format(ref_server, 'OperationOutcome', new_bundle.id)
    entry.resource = OO.OperationOutcome(json.loads(f.oo_template))  # make a fixed template for now
    entry.search = Bundle.BundleEntrySearch({'mode':'outcome'})
    new_bundle.entry.append(entry)
    return(new_bundle)

application = Flask(__name__)


@application.route('/', methods=['GET', 'POST'])  # decorator to map to home page
def index():
    global ref_server
    if request.method == 'POST':
        ref_server = request.form['options']
    return render_template('index.html', ref_server = ref_server)

@application.route('/<rt>')  # decorator to map for a FHIR Resource search endpoint
def fhir_search(rt):  # rt = resource type
    # check if is valid resource
    sp = dict(request.args)  # sp = search parameters everything after the ?
    # searchword = request.args.get('x', '')
    status_code, reason, headers, res_json, res_id, res_narr = search(ref_server, rt, sp) # return a tuple access with usual operations  note the json.dumps(dict(r.headers)) make case insensitive dict makes possible to dump
    return f.search_bundle_return.format(rt, sp, status_code, reason, json.dumps(dict(headers), sort_keys=True, indent=4), res_id, res_narr, json.dumps(dict(res_json), sort_keys=True, indent=4))

@application.route('/<rt>/<r_id>')  # decorator to map for a FHIR Resource fetch endpoint
def fhir_fetch(rt, r_id):  # rt = resource type id = resource id
    # check if is valid resource
    sp = dict(request.args)  # sp = search parameters everything after the ?
    sp['_id'] = r_id
    status_code, reason, headers, res_json, res_id, res_narr = search(ref_server, rt, sp) # return a tuple access with usual operations  note the json.dumps(dict(r.headers)) make case insensitive dict makes possible to dump
    return f.fetch_resource_return.format(rt, r_id, status_code, reason, json.dumps(dict(headers), sort_keys=True, indent=4),res_id, res_narr, json.dumps(dict(res_json), sort_keys=True, indent=4))

@application.route('/Appointment/$find', methods=['GET', 'POST'])  # decorator to map for Appointment availability operation
def Appt_find(): # fhir_op = appt operation find|hold|book
    '''
    General approach is to find the slots, create the Appt resources, Post to server and present to user
    Todo iterate throught schedule.actors
    Todo append all practs and orgs to a single list of slots and then compare to locations. stop when find enough.
    '''
    rt = 'Appointment'  # rt = resource type
    op = dict(request.args)
    slots = []
    p_slots = []
    l_slots = []
    appts=[]
    try:
        for actor in op['practitioner']:
            p_slots = p_slots + get_slots(op,actor)
    except KeyError:  # no pract specified
        pass
    try:
        for actor in op['organization']:
            p_slots = p_slots + get_slots(op,actor)
    except KeyError:  # no org specified
        pass
    try:
        for actor in op['location-reference']:
            l_slots = l_slots + get_slots(op,actor)
    except KeyError:  # no location specified
        pass
    # filter by pract AND location
    # loop through all the practitioner slots and compare to all location slots then loop back through the filtered locations to get the practiioner slots
    if p_slots and l_slots:
        for ps in p_slots:
            slots = [ls for ls in l_slots if ls.start == ps.start]  #  use the start times for now
        for ls in slots:
            slots = [ps for ps in p_slots if ls.start == ps.start]  #  use the start times for now
    elif not p_slots and not l_slots:  # no actors
        slots = slots + get_slots(op)
    else:
        slots= p_slots + l_slots
    # status_code, reason, headers, res_json, res_id, res_narr = search(ref_server, 'Slot', slot_sp)  # return a tuple access with usual operations  note the json.dumps(idict(r.headers)) make case insensitive dict makes possible to dump

    # filter slots for specialty - since not a standard FHIR search parameter
    try:
        for op_specialty in op['specialty']:
            # logging.info('code={} of type {} and op_specialty={} of type {}'.format(slots[0].specialty[0].coding[0].code, type(slots[0].specialty[0].coding[0].code),type(op_specialty.split('|')[0]), op_specialty.split('|')[-1]))
            slots = [s for s in slots if s.specialty[0].coding[0].code == op_specialty.split('|')[-1]]
                #and code.system == specialty.split('|')[0]) for system  and for further repeats todo later
    except KeyError:  # no specialty specified
        pass

    #construct the Appointment from the slots.
    for slot in slots[0:count]:  # only the first three
        appts.append(make_appts(op,slot))
    # and package in a bundle
    aa_bundle = aa_bundler(appts)

    try:
        return f.operation_find_return.format('Slot', op, len(slots), [s.as_json() for s in slots], json.dumps(aa_bundle.as_json(), sort_keys=True, indent=4))
    except TypeError:
        return f.operation_find_exception_return.format('Slot', op)

@application.route('/Appointment/$hold', methods=['POST'])  # decorator to map for Appointment hold operation
def Appt_hold():
    '''
    General approach is to...
    '''
    rt = 'Appointment'  # rt = resource typei
    op = dict(request.args)
    return f.operation_hold_return.format(rt, '$hold', request.url, request.method, op)

@application.route('/Appointment/$book', methods=['POST'])  # decorator to map for Appointment hold operation
def Appt_book():
    '''
    General approach is to...
    '''
    rt = 'Appointment'  # rt = resource type
    op = dict(request.args)
    return f.operation_hold_return.format(rt, '$book', request.url, request.method, op)

# run the app.
if __name__ == "__main__":
    # Setting debug to True enables debug output. This line should be
    # removed before deploying a production app.
    application.debug = True
    application.run()
