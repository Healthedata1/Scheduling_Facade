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
import fhirclient.models.parameters as Param
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

    try:  # visit-types
        f.slot_sp['slot-type'] = [k for k in op['visit-type']]
    except KeyError:
        pass

    f.slot_sp['schedule.actor'] = actor
    logging.info('actor = {} of type = {} '.format(actor, type(actor)))
    try:  # date params for slot and schedule
        f.slot_sp['start'] = ['ge' + k for k in op['start']]
    except KeyError:
        pass

    try:  # date params for slot and schedule
        f.slot_sp['start'] = f.slot_sp['start'] + ['le' + k for k in op['end']]
    except KeyError:
        pass

    try:  # may get rid of this and apply at the end.
        f.slot_sp['_count'] = op['_count']
    except KeyError:
        pass
    return(f.slot_sp)


def search(ref_server, res_type, sp={}):
    res_id = []
    url = '{}/{}'.format(ref_server, res_type)
    logging.info('sp = {}  url = {}'.format(sp, url))
    r = requests.get(url, headers=f.headers, params=sp)
    # Return server response ...
    try:
        res_id = [i['resource']['id'] for i in r.json()['entry']]
    except KeyError:
        logging.info("res_id failed :-(")
        pass
    except ValueError:
        logging.info('res_id failed :-( poss includes simplejson.decoder.JSONDecodeError')
        pass
    try:
        res_narr = [i['resource']['text']['div'] for i in r.json()['entry']]
    except KeyError:
        logging.info('res_id failed :-( poss includes simplejson.decoder.JSONDecodeError')
        pass
    except ValueError:  # includes simplejson.decoder.JSONDecodeError
        logging.info('res_narr failed :-( poss includes simplejson.decoder.JSONDecodeError')
        pass
    try:
        return(r.status_code, r.reason, r.headers, r.json(), res_id, res_narr) # return a tuple access with usual operations
        logging.info("successful GET!!")
    except:
        logging.info("unsuccessful GET :-( status code = {}, reason = {} and headers = {}".format(r.status_code, r.reason, r.headers))

        return(r.status_code, r.reason, r.headers, {}, None, None)  # return a tuple access with usual operations  note the json.dumps(dict(r.headers)) make case insensitive dict makes possible to dump

def post_appt(resources):
    ''' upload pending appts to ref_server:
        create transation bundle
        post transaction
        return operation outcome'''

    data = bundler(resources,'tr').as_json()
    logging.info('bundle = {}'.format(json.dumps(data)))
    r = requests.post(ref_server, headers=f.headers, data = json.dumps(data))
    logging.info('url= {}\nr.status_code ={}\nr.reason={}\nr.headers=\nr.json()={}'.format(ref_server,r.status_code, r.reason, r.headers, r.json()))
    return (r.status_code, r.reason, r.headers, r.json())


def timestamp():
    # get url freindly time stamp
    dts = str(datetime.datetime.utcnow().isoformat())
    dts = dts.replace(':', '')
    dts = dts.replace('.', '')
    return dts


def status_check(ref):  # fetch resources and check for for slots in bundle check if SLot status == "free"  and Appointment is "proposed" if all good then do a PUT transaction with updated status of "pending" TODO update the participant statuses
    logging.info('starting status_check...')
    res_json = []
    r = requests.get(url='{}/{}'.format(ref_server,ref), headers=f.headers) # fetch appointment
    appointment=Appt.Appointment(r.json())

    logging.info('appt={}\n of type= {} with id ={}'.format(appointment.as_json(), type(appointment), appointment.id))

    slots=[]
    # get the list of slots from the appointment
    for slot_ref in appointment.slot:
        logging.info('slot as dict ={}'.format(slot_ref.as_json()))
        ref = FRef.FHIRReference(slot_ref.as_json()).reference
        logging.info('ref={}'.format(ref))
        r = requests.get(url='{}/{}'.format(ref_server,ref),  headers=f.headers) # fetch slot
        slot=Slot.Slot(r.json())
        slots.append(slot)
        logging.info('slot={}'.format(slots[-1].as_json()))

    #if hold:  ( do this for book too)
    if appointment.status == 'proposed' and all(slot.status in ['free', 'busy-tentative'] for slot in slots): # NOTE in brian's server updates automatically upon posting appointments.  so assume for now that busy-tentative = free  and imagine update statuses  busy-tentative
            logging.info('update statuses...')
            appointment.status = 'pending' # update statuses
            appointment.text = None # strip text  adn let server update
            # TODO update actor statuses to 'tentative'
            for slot in slots:
                slot.status = "busy-tentative"  # **** NOTE *** brian's server updates automatically upon posting appointments.  so assume for now that busy-tentative = free update statuses and update to busey - unavailable
                slot.text = None # strip narrative let server update

    else:
        logging.info('hold rejected...')
        return (False)  # hold rejected

    post_appt([appointment] + slots)
    return (True) # hold completed


def get_slots(op, actor=None):
    slot_sp = slot_sp_convert(op, actor)  # dict of search params converted to FHIR search param for slot
    logging.info('converted op to sp')
    res_json = search(ref_server, 'Slot', slot_sp)[3]
    logging.info('fetching slots from ref server: res_json={}'.format(json.dumps(res_json)))
    return unbundle(res_json)

def unbundle(res_json):
    try:  # unbundle res from search results and add to the res list
        bundle = Bundle.Bundle(res_json)
        res = [be.resource for be in bundle.entry]
    # logging.info('slots[0] is: {}'.format(slots[0].as_json()))
        return(res)
    except:
        logging.info('return None if bundle is None or no bundle entries')
        return(None)

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
    appt.id = '{}{}'.format( slot.id,timestamp())
    appt.status = 'proposed'
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
    appt.slot = [FRef.FHIRReference({'reference': 'Slot/{}'.format(slot.id)})]  # option a

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
        for url in op['patient-reference']: #TODO add patient stub in for now
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


def bundler(resources, type='aa'):  # make the operation output type = 'aa' or transactions bundle type = 'tr'
    logging.info("starting bundler...")
    new_bundle = Bundle.Bundle()
    new_bundle.id = 'argo-{}b-{}'.format(type, timestamp())
    new_bundle.type = f.bundle_type[type]
    new_bundle.entry = []
    for res in resources:  #  list of resources
        logging.info('res ={}'.format(res))
        entry = Bundle.BundleEntry()
        entry.fullUrl = '{}/{}/{}'.format(ref_server, res.resource_type, res.id)
        entry.resource = res
        if type == 'aa':
            entry.search = Bundle.BundleEntrySearch({'mode':'match'})
        if type == 'tr':
            trans = Bundle.BundleEntryRequest()
            trans.method = 'PUT'
            trans.url = '{}/{}'.format(res.resource_type,res.id)
            entry.request = trans
        new_bundle.entry.append(entry)
    if type == 'aa':
        new_bundle.total = len(resources)  # need to keep count same a op parameter
        # OO stubbed in here:
        entry = Bundle.BundleEntry()
        entry.fullUrl = '{}/{}/{}'.format(ref_server, 'OperationOutcome', new_bundle.id)
        entry.resource = OO.OperationOutcome(json.loads(f.oo_template))  # make a fixed template for now
        entry.search = Bundle.BundleEntrySearch({'mode':'outcome'})
        new_bundle.entry.append(entry)
    logging.info('new_bundle={}'.format(new_bundle.as_json()))
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

    res = requests.get(url='{}/{}/{}'.format(ref_server,rt,r_id), headers=f.headers) # fetch resource by id
    res_narr = res.json()['text']['div']

    return f.fetch_resource_return.format(rt, r_id, res_narr, json.dumps(dict(res.json()), sort_keys=True, indent=4))

@application.route('/Appointment/$find')  # decorator to map for Appointment availability operation  TODO add POST capabilities
def Appt_find(): # fhir_op = appt operation find|hold|book
    '''
    General approach is to find the slots, create the Appt resources, Post to server and present to user
    Todo iterate throught schedule.actors
    Todo append all practs and orgs to a single list of slots and then compare to locations. stop when find enough.
    '''
    rt = 'Appointment'  # rt = resource type
    op = dict(request.args)
    logging.info('these are the operation arguments:{}'.format(op))
    slots = []
    p_slots = []
    l_slots = []
    appts=[]
    try:
        for actor in op['practitioner']:
            p_slots = p_slots + get_slots(op, actor)
    except (KeyError, TypeError):  # no pract specified or null slots returned
        logging.info('no pract specified or null slots returned')
        pass
    try:
        for actor in op['organization']:
            p_slots = p_slots + get_slots(op,actor)
    except (KeyError, TypeError):  # no pract specified or null slots returned
        logging.info('no org specified or null slots returned')
        pass
    try:
        for actor in op['location-reference']:
            l_slots = l_slots + get_slots(op,actor)
    except (KeyError, TypeError):  # no pract specified or null slots returned
        logging.info('no loc specified or null slots returned')
        pass

    if p_slots and l_slots:
        # filter by pract AND location
        # loop through all the practitioner slots and compare to all location slots then loop back through the filtered locations to get the practiioner slots
        slots = [l for l in l_slots if any(l.start == p.start for p in p_slots)]  # use the start times for now
        slots = [p for p in p_slots if any(p.start == s.start for s in slots)]
    elif not p_slots and not l_slots:  # no actors
        slots = slots + get_slots(op)
    else:
        slots= p_slots + l_slots  # loc or pract/org search
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
    for slot in slots:  # for slot in slots[i0:count] to choke down to only the first three
        appts.append(make_appts(op,slot))
    # and package in a bundle
    # aa_bundle = bundler(appts, 'aa')  # make searchset bundle to display to end user
    post_appt(appts)  # upload pending appts to ref_server

    # get search bundle back with Appointments

    id_sp = {'_id':','.join([appt.id for appt in appts])} # get appt ids for search ad ?_id=id1,id2,id3,...
    logging.info('id_sp = {}'.format(id_sp))
    status_code, reason, headers, res_json, res_id, res_narr = search(ref_server, rt, id_sp) # return a tuple access with usual operations  note the json.dumps(dict(r.headers)) make case insensitive dict makes possible to dump# get appts from the ref_server


    try:
        return f.operation_find_return.format( op, '<ol><li>{}</li></ol>'.format('</li><li>'.join([i for i in res_id])), '<ol><li>{}</li></ol>'.format('</li> <li>'.join([i for i in res_narr])), json.dumps(dict(res_json), sort_keys=True, indent=4))
    except TypeError:
        return f.operation_find_exception_return.format(op)

@application.route('/Appointment/$hold', methods=['POST'])  # decorator to map for Appointment hold operation
def Appt_hold():
    logging.info('operation $hold...')
    '''
    General approach is to get the appt and fetch all the associated slots.   (include is not an option here) check if statuses are ok if so then update statuses if not then don't update :-(
    hold input parameters:
    1. appt-id  - this use case map to _id sp
    2. appt-resource ( for prefetching )  not use here
    return an appt avaiability bundle
    '''
    rt = 'Appointment'  # rt = resource typei
    content = request.get_json()
    # logging.info('content = {} type ={}'.format(content ,type(content)))
    params = Param.Parameters(content)
    # logging.info('params.parameter[0].valueUri = {} less Appointment/ ={} '.format(params.parameter[0].valueUri, params.parameter[0].valueUri.split('Appointment/')[-1]))
    appt_ref = params.parameter[0].valueUri  #map op to sp assuming is relative ref.

    logging.info('appt = {}'.format(appt_ref))
    if status_check(appt_ref):   #for search and for slots in bundle check if status == "free"  and Appointment is "proposed" update all to pending
        status_code, reason, headers, res_json, res_id, res_narr = search(ref_server, rt, sp={'_id': appt_ref.split('/')[-1]}) # retrieve teh search bundle from the ref server using the id only
        return f.operation_hold_confirm.format(rt, '$hold', appt_ref, res_narr[0], json.dumps(dict(res_json), sort_keys=True, indent=4))
    else: # if none type or unable to hold
        return f.operation_hold_reject.format(rt, '$hold', rt, params.parameter[0].valueUri)

@application.route('/Appointment/$book', methods=['POST'])  # decorator to map for Appointment hold operation
def Appt_book():
    '''
    General approach is to .same as hold except update from pending to booked
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
