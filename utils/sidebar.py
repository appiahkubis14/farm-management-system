# utils/sidebar.py
from enum import Enum

class Sidebar:
    sidebar_items = {
        "Dashboard": {
            "icon": "fas fa-chart-pie",
            "url": "/dashboard/", 
            "groups": ["Admin", "Project Officer", "Regional Manager", "Monitoring and Evaluation", "District Officer", "Project Coordinator", "Project Manager", "National"],
        },
        
        "Farm Management": {
            "icon": "fas fa-tractor",
            "groups": ["Admin", "Project Officer", "Monitoring and Evaluation", "District Officer", "Project Coordinator"],
            "sub_items": {
                "Farms Overview": {
                    "icon": "fas fa-database", 
                    "url": "/farm-management/farms/", 
                    "groups": ["Admin", "Project Officer", "Monitoring and Evaluation", "District Officer"]
                },
                "Farm Mapping": {
                    "icon": "fas fa-map-marked-alt", 
                    "url": "/farm-management/mapped-farms/", 
                    "groups": ["Admin", "Project Officer", "Monitoring and Evaluation"]
                },
                "Farm Assignments": {
                    "icon": "fas fa-user-check", 
                    "url": "/farm-management/farm-assignment/", 
                    "groups": ["Admin", "Project Officer", "Project Coordinator"]
                },
            }
        },
        "QR Code Generator":{
            "icon": "fas fa-qrcode",
            'url': "/qr-code-generator/",
            'groups': ["Admin", "Project Officer", "Monitoring and Evaluation", "District Officer", "Project Coordinator"]
        },

        "Sensors & IoT System": {
            "icon": "fas fa-microchip",
            "groups": ["Admin", "Project Officer", "Monitoring and Evaluation", "Regional Manager"],
            "sub_items": {
                "Sensor Dashboard": {
                    "icon": "fas fa-tachometer-alt", 
                    "url": "/sensors/dashboard/", 
                    "groups": ["Admin", "Project Officer", "Monitoring and Evaluation", "Regional Manager"]
                },
                "Sensor Management": {
                    "icon": "fas fa-cogs", 
                    "url": "/sensors/devices/management/", 
                    "groups": ["Admin", "Project Officer", "Monitoring and Evaluation"]
                },
                "Data Logs": {
                    "icon": "fas fa-file-alt", 
                    "url": "/sensors/data-logs/", 
                    "groups": ["Admin", "Monitoring and Evaluation", "Regional Manager"]
                },
            }
        },
        
        "Activities & Reporting": {
            "icon": "fas fa-clipboard-check",
            "groups": ["Admin", "Project Officer", "Monitoring and Evaluation", "District Officer", "Regional Manager"],
            "sub_items": {
                "Activities Overview": {
                    "icon": "fas fa-tasks", 
                    "url": "/activities/activities/", 
                    "groups": ["Admin", "Monitoring and Evaluation"]
                },
                "Daily Reports": {
                    "icon": "fas fa-calendar-day", 
                    "url": "/activities/po-daily-reports/", 
                    "groups": ["Admin", "Project Officer", "Monitoring and Evaluation"]
                },
                "Activity Reporting": {
                    "icon": "fas fa-file-upload", 
                    "url": "/activities/activity-reporting/", 
                    "groups": ["Admin", "Project Officer", "Monitoring and Evaluation"]
                },
                "Weekly Monitoring": {
                    "icon": "fas fa-calendar-week", 
                    "url": "/activities/weekly-monitoring/", 
                    "groups": ["Admin", "Project Officer", "Monitoring and Evaluation", "Regional Manager"]
                },
                "Activity Rates": {
                    "icon": "fas fa-money-bill-wave", 
                    "url": "/activities/rates/", 
                    "groups": ["Admin", "Monitoring and Evaluation", "Regional Manager"]
                },
            }
        },
        
        "Personnel Management": {
            "icon": "fas fa-users-cog",
            "groups": ["Admin", "Project Officer", "Project Coordinator", "Regional Manager"],
            "sub_items": {
                "Staff Overview": {
                    "icon": "fas fa-user-tie", 
                    "url": "/personnel/staff/", 
                    "groups": ["Admin", "Project Coordinator", "Regional Manager"]
                },
                "Rehab Assistants": {
                    "icon": "fas fa-user-friends", 
                    "url": "/personnel/rehab-assistants/", 
                    "groups": ["Admin", "Project Officer", "Project Coordinator"]
                },
                "Contractors": {
                    "icon": "fas fa-handshake", 
                    "url": "/personnel/contractors/", 
                    "groups": ["Admin", "Project Officer", "Project Coordinator"]
                },
                "Staff Assignments": {
                    "icon": "fas fa-user-tag", 
                    "url": "/personnel/assignments/",
                    "groups": ["Admin", "Project Coordinator"]
                },
            }
        },
        
        "Monitoring & Validation": {
            "icon": "fas fa-search",
            "groups": ["Admin", "Monitoring and Evaluation", "Regional Manager", "Project Manager"],
            "sub_items": {
                "Farm Validation": {
                    "icon": "fas fa-clipboard-check", 
                    "url": "/monitoring/farm-validation/", 
                    "groups": ["Admin", "Monitoring and Evaluation"]
                },
                "Seedling Enumeration": {
                    "icon": "fas fa-seedling", 
                    "url": "/monitoring/seedling-enumeration/", 
                    "groups": ["Admin", "Monitoring and Evaluation", "Project Officer"]
                },
                "Verification Workdone": {
                    "icon": "fas fa-check-circle", 
                    "url": "/monitoring/verification-workdone/", 
                    "groups": ["Admin", "Monitoring and Evaluation", "Regional Manager"]
                },
                "PO Route Monitoring": {
                    "icon": "fas fa-route", 
                    "url": "/monitoring/po-route-monitoring/", 
                    "groups": ["Admin", "Monitoring and Evaluation", "Regional Manager"]
                },
                "ODK Integration": {
                    "icon": "fas fa-sync-alt", 
                    "url": "/monitoring/odk-urls/", 
                    "groups": ["Admin", "Monitoring and Evaluation"]
                },
            }
        },
        
        "Certification & Payment": {
            "icon": "fas fa-file-invoice-dollar",
            "groups": ["Admin", "Project Officer", "Monitoring and Evaluation", "Regional Manager", "Project Manager"],
            "sub_items": {
                "Work Certificates": {
                    "icon": "fas fa-file-certificate", 
                    "url": "/certification/ched-certificates/", 
                    "groups": ["Admin", "Project Officer", "Monitoring and Evaluation"]
                },
                "Payment Reports": {
                    "icon": "fas fa-file-invoice", 
                    "url": "/payment/payment-reports/", 
                    "groups": ["Admin", "Project Officer", "Regional Manager"]
                },
                "Detailed Payments": {
                    "icon": "fas fa-file-invoice-dollar", 
                    "url": "/payment/detailed-reports/", 
                    "groups": ["Admin", "Project Officer", "Regional Manager"]
                },
                "CalBank Transactions": {
                    "icon": "fas fa-mobile-alt", 
                    "url": "/payment/calbank-transactions/", 
                    "groups": ["Admin", "Project Manager"]
                },
                "Equipment": {
                    "icon": "fas fa-tools", 
                    "url": "/equipment/equipment/", 
                    "groups": ["Admin", "Project Officer", "Monitoring and Evaluation"]
                },
            }
        },
        
        "Reports & Analytics": {
            "icon": "fas fa-chart-bar",
            "groups": ["Admin", "Monitoring and Evaluation", "Regional Manager", "Project Manager", "National"],
            "sub_items": {
                "Weekly Summary": {
                    "icon": "fas fa-chart-line", 
                    "url": "/reports/weekly-summary/", 
                    "groups": ["Admin", "Monitoring and Evaluation", "Regional Manager"]
                },
                "Farm Database": {
                    "icon": "fas fa-database", 
                    "url": "/reports/farm-database/", 
                    "groups": ["Admin", "Monitoring and Evaluation", "Regional Manager"]
                },
               
            }
        },
        
        # "System": {
        #     "icon": "fas fa-cogs",
        #     "groups": ["Admin"],
        #     "sub_items": {
        #         "Users": {
        #             "icon": "fas fa-user-cog", 
        #             "url": "/admin/auth/user/", 
        #             "groups": ["Admin"]
        #         },
        #         "Groups": {
        #             "icon": "fas fa-users", 
        #             "url": "/admin/auth/group/", 
        #             "groups": ["Admin"]
        #         },
        #         "Menu Configuration": {
        #             "icon": "fas fa-bars", 
        #             "url": "/admin/system/sidebar/", 
        #             "groups": ["Admin"]
        #         },
        #         "Background Tasks": {
        #             "icon": "fas fa-tasks", 
        #             "url": "/admin/system/background-tasks/", 
        #             "groups": ["Admin"]
        #         },
        #         "System Info": {
        #             "icon": "fas fa-code-branch", 
        #             "url": "/admin/system/version/", 
        #             "groups": ["Admin"]
        #         },
        #     }
        # },
        
        # "Feedback": {
        #     "icon": "fas fa-comments",
        #     "url": "/feedback/",
        #     "groups": ["Admin", "Project Officer", "Monitoring and Evaluation", "District Officer", "Regional Manager"]
        # },
        
        "Admin": {
            "icon": "fas fa-user-shield",
            "url": "/admin/",
            "groups": ["Admin"]
        }
    }