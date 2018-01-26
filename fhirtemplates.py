# fhir-templates.py
# entry_template not used
entry_template = '''
    {{
      "fullUrl": "https://example.com/base/Appointment/{entry_id}",
      "resource":
      {bundle_entry}
      "search": {{
        "mode": "match"
      }}
    }},
    '''
# bundle_template not used
bundle_template = '''
{{
  "resourceType": "Bundle",
  "id": "{bundle_id}",
  "meta": {{
    "profile": [
      "http://fhir.org/guides/argonaut-scheduling/StructureDefinition/avail-bundle"
    ]
  }},
  "type": "searchset",
  "total": {bundle_total:d},
  "entry": [
    {{ {bundle_entries}
    }},
    {{
      "fullUrl": "https://example.com/base/OperationOutcome/{oo_id}",
      "resource": {{
        "resourceType": "OperationOutcome",
        "id": "{oo_id}",
        "text": {{
          "status": "generated",
          "div": "<div xmlns=\"http://www.w3.org/1999/xhtml\"><p><b>Generated Narrative with Details</b></p><p><b>id</b>: example</p><h3>Issues</h3><table class=\"grid\"><tr><td>-</td><td><b>Severity</b></td><td><b>Code</b></td><td><b>Details</b></td></tr><tr><td>*</td><td>information</td><td>informational</td><td>the appointment availability operation was successful <span style=\"background: LightGoldenRodYellow\">(Details )</span></td></tr></table></div>"
        }},
        "issue": [
          {{
            "severity": "information",
            "code": "informational",
            "details": {{
              "text": "the appointment availability operation was successful"
            }}
          }}
        ]
      }},
      "search": {{
        "mode": "outcome"
      }}
    }}
  ]
}}
'''
# appt_template not used
appt_template = '''
{{
  "resourceType": "Appointment",
  "id": "{appt_id}",
  "meta": {{
    "profile": [
      "http://fhir.org/guides/argonaut-scheduling/StructureDefinition/appt-output"
    ]
  }},
  "created" : "{created_dt}",
  "status": "proposed",
  "serviceType": [
    {{
      "coding": [
        {{
          "system": "http://snomed.info/sct",
          "code": "{service_code}",
          "display": "{service_display}"
        }}
      ],
      "text": "{service_text}"
    }}
  ],
  "specialty": [
    {{
      "coding": [
        {{
          "system": "http://snomed.info/sct",
          "code": "{specialty_code}",
          "display": "{specialty_display}"
        }}
      ],
      "text": "{specialty_text}"
    }}
  ],
  "appointmentType": {{
    "coding": [
      {{
        "system": "http://hl7.org/fhir/v2/0276",
        "code": "{appt_type_code}"
      }}
    ],
    "text": "{appt_type_text}"
  }},
  "start": "{appt_start}",
  "end": "{appt_end}",
  "slot" : [
    {{
       "reference": "Slot/{slot_id}",
       "display": "{slot_display}"
    }}
    ],
  "participant": [
    {{
      "actor": {{
        "reference": "Practitioner/{pract_id}",
        "display": "{pract_display}"
      }},
      "required": "required",
      "status": "needs-action"
    }},
    {{
      "actor": {{
        "display": "{location}"
      }},
      "required": "required",
      "status": "needs-action"
    }}
  ],
  "requestedPeriod": [
    {{
      "start": "{req_start}",
      "end": "{req_end}"
    }}
  ]
}}
'''
# data not used
data = {
    'service_code': '',
    'service_display': '',
    'service_text': '',
    'specialty_code': '',
    'specialty_display': '',
    'specialty_text': '',
    'appt_type_code': '',
    'appt_type_text': '',
    'pract_id': '',
    'pract_display': '',
    'location': '',
    'req_start': '',
    'req_end': ''
}

# slot_bundle example for testing
slot_bundle = '''{
    "resourceType": "Bundle",
    "id": "urn:uuid:284134a1c9044e27abb04bf39a2d3c52",
    "meta": {
        "lastUpdated": "2018-01-24T23:39:14.568+00:00"
    },
    "type": "searchset",
    "total": 1689,
    "link": [
        {
            "relation": "self",
            "url": "http://sqlonfhir-stu3.azurewebsites.net/fhir/Slot?status=free&_count=3&_snapshot=636524339545687756"
        },
        {
            "relation": "first",
            "url": "http://sqlonfhir-stu3.azurewebsites.net/fhir/Slot?status=free&_count=3&_snapshot=636524339545687756"
        },
        {
            "relation": "next",
            "url": "http://sqlonfhir-stu3.azurewebsites.net/fhir/Slot?status=free&_count=3&_snapshot=636524339545687756&_page=1"
        },
        {
            "relation": "last",
            "url": "http://sqlonfhir-stu3.azurewebsites.net/fhir/Slot?status=free&_count=3&_snapshot=636524339545687756&_page=563"
        }
    ],
    "entry": [
        {
            "fullUrl": "http://sqlonfhir-stu3.azurewebsites.net/fhir/Slot/2017-09-07T153000-arg-s-6",
            "resource": {
                "resourceType": "Slot",
                "id": "2017-09-07T153000-arg-s-6",
                "meta": {
                    "versionId": "4",
                    "lastUpdated": "2017-09-08T00:02:22.776+00:00"
                },
                "text": {
                    "status": "generated",
                    "div": "<div xmlns=\"http://www.w3.org/1999/xhtml\">\r\n      Thu Sep  7 15:30:00 2017-Thu Sep  7 15:45:00 2017: <b> free</b> Family Medicine\r\n    </div>"
                },
                "specialty": [
                    {
                        "coding": [
                            {
                                "code": "419772000",
                                "display": "Family Medicine"
                            }
                        ]
                    }
                ],
                "appointmentType": {
                    "coding": [
                        {
                            "system": "http://hl7.org/fhir/v2/0276",
                            "code": "ROUTINE",
                            "display": "Routine appointment - default if not valued"
                        }
                    ]
                },
                "schedule": {
                    "reference": "Schedule/arg-s-6"
                },
                "status": "free",
                "start": "2017-09-07T15:30:00+00:00",
                "end": "2017-09-07T15:45:00+00:00"
            }
        },
        {
            "fullUrl": "http://sqlonfhir-stu3.azurewebsites.net/fhir/Slot/2017-09-07T151500-arg-s-6",
            "resource": {
                "resourceType": "Slot",
                "id": "2017-09-07T151500-arg-s-6",
                "meta": {
                    "versionId": "4",
                    "lastUpdated": "2017-09-08T00:02:22.526+00:00"
                },
                "text": {
                    "status": "generated",
                    "div": "<div xmlns=\"http://www.w3.org/1999/xhtml\">\r\n      Thu Sep  7 15:15:00 2017-Thu Sep  7 15:30:00 2017: <b> free</b> Family Medicine\r\n    </div>"
                },
                "specialty": [
                    {
                        "coding": [
                            {
                                "code": "419772000",
                                "display": "Family Medicine"
                            }
                        ]
                    }
                ],
                "appointmentType": {
                    "coding": [
                        {
                            "system": "http://hl7.org/fhir/v2/0276",
                            "code": "ROUTINE",
                            "display": "Routine appointment - default if not valued"
                        }
                    ]
                },
                "schedule": {
                    "reference": "Schedule/arg-s-6"
                },
                "status": "free",
                "start": "2017-09-07T15:15:00+00:00",
                "end": "2017-09-07T15:30:00+00:00"
            }
        },
        {
            "fullUrl": "http://sqlonfhir-stu3.azurewebsites.net/fhir/Slot/2017-09-07T150000-arg-s-6",
            "resource": {
                "resourceType": "Slot",
                "id": "2017-09-07T150000-arg-s-6",
                "meta": {
                    "versionId": "4",
                    "lastUpdated": "2017-09-08T00:02:22.292+00:00"
                },
                "text": {
                    "status": "generated",
                    "div": "<div xmlns=\"http://www.w3.org/1999/xhtml\">\r\n      Thu Sep  7 15:00:00 2017-Thu Sep  7 15:15:00 2017: <b> free</b> Family Medicine\r\n    </div>"
                },
                "specialty": [
                    {
                        "coding": [
                            {
                                "code": "419772000",
                                "display": "Family Medicine"
                            }
                        ]
                    }
                ],
                "appointmentType": {
                    "coding": [
                        {
                            "system": "http://hl7.org/fhir/v2/0276",
                            "code": "ROUTINE",
                            "display": "Routine appointment - default if not valued"
                        }
                    ]
                },
                "schedule": {
                    "reference": "Schedule/arg-s-6"
                },
                "status": "free",
                "start": "2017-09-07T15:00:00+00:00",
                "end": "2017-09-07T15:15:00+00:00"
            }
        }
    ]
}
'''
# oo_template as a stub for now
oo_template = '''
{
        "resourceType" : "OperationOutcome",
        "id" : "example",
        "issue" : [
          {
            "severity" : "information",
            "code" : "informational",
            "details" : {
              "text" : "the appointment availability operation was successful"
            }
          }
        ]
      }
'''

search_bundle_return = '''
<h1>Search bundle for the {} resource with these search parameters {}:</h1>
<br />
<strong>status code</strong> = {}
<br />
reason = {}
<br />
headers = <pre>{}</pre>
<br />
<strong>Resource id</strong> = {}
<br />
<strong>Resource narrative</strong> = {}
<br />
<strong>Resource as json</strong> =<pre>{}</pre>
'''

fetch_resource_return = '''
<h3>Fetched the {}/{} resource:</h3>
<br />
<strong>status code</strong> = {}
<br />
<strong>reason</strong> = {}
<br />
<strong>headers</strong> = <pre>{}</pre>
<br />
<strong>resource id</strong> = {}
<br />
<strong>resource narrative</strong> = {}
<br />
<strong>resource as json</strong> = <pre>{}</pre>
'''

operation_find_return = '''
<?xml version="1.0" encoding="UTF-8"?>
<h3>Operation $find returns the Search bundle for the Appointment resource with the operation parameters: {}:</h3>
<ul>
<li>
<strong>Appt resource ids </strong>: {}
</li>
<li>
<strong>Appt resource narratives </strong>: {}
</li>
<li>
<strong>Appt Output Bundle as json </strong>: <pre>{}</pre>
</li>
</ul>
'''

operation_find_exception_return = '''
<h3>Operation $find returns the Search bundle for the Appointment resource with the operation parameters: {}:</h3>
<br />
No Appointments for those input parameters :-(
'''

operation_hold_return ='''
<?xml version="1.0" encoding="UTF-8"?>'This is the {} {} operation with this {} url using the {} method and these filter parameters {}
'''

bundle_type = {'aa': 'searchset', 'tr': 'transaction'}

headers = {'Content-Type': 'application/fhir+json', 'Accept': 'application/fhir+json'}

slot_sp = {
    'slot-type': [],
    'schedule.actor': None,
    'start': [],
    'status': 'free',  # fixed for now
    '_count': 3  # fix to 3 for testing
    }
