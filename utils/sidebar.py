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
                # "Job Orders": {
                #     "icon": "fas fa-clipboard-list", 
                #     "url": "/farm-management/job-orders/", 
                #     "groups": ["Admin", "Project Officer", "Project Coordinator"]
                # },
                "Farm Assignments": {
                    "icon": "fas fa-user-check", 
                    "url": "/farm-management/farm-assignment/", 
                    "groups": ["Admin", "Project Officer", "Project Coordinator"]
                },
            }
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
                "Activities Master": {
                    "icon": "fas fa-tasks", 
                    "url": "/activities/activities/", 
                    "groups": ["Admin", "Monitoring and Evaluation"]
                },
                "Activity Rates": {
                    "icon": "fas fa-money-bill-wave", 
                    "url": "/activities/rates/", 
                    "groups": ["Admin", "Monitoring and Evaluation", "Regional Manager"]
                },
                "Weekly Monitoring": {
                    "icon": "fas fa-calendar-week", 
                    "url": "/activities/weekly-monitoring/", 
                    "groups": ["Admin", "Project Officer", "Monitoring and Evaluation", "Regional Manager"]
                },
                "Daily PO Reports": {
                    "icon": "fas fa-calendar-day", 
                    "url": "/activities/po-daily-reports/", 
                    "groups": ["Admin", "Project Officer", "Monitoring and Evaluation"]
                },
                "Activity Reporting (New)": {
                    "icon": "fas fa-file-upload", 
                    "url": "/activities/activity-reporting/", 
                    "groups": ["Admin", "Project Officer", "Monitoring and Evaluation"]
                },
                "Mobile Maintenance": {
                    "icon": "fas fa-mobile-alt", 
                    "url": "/activities/mobile-maintenance/", 
                    "groups": ["Admin", "Project Officer", "Monitoring and Evaluation"]
                },
            }
        },
        
        "Personnel Management": {
            "icon": "fas fa-users-cog",
            "groups": ["Admin", "Project Officer", "Project Coordinator", "Regional Manager"],
            "sub_items": {
                "Staff Management": {
                    "icon": "fas fa-user-tie", 
                    "url": "/personnel/staff/", 
                    "groups": ["Admin", "Project Coordinator", "Regional Manager"]
                },
                "Rehab Assistants": {
                    "icon": "fas fa-user-friends", 
                    "url": "/personnel/rehab-assistants/", 
                    "groups": ["Admin", "Project Officer", "Project Coordinator"]
                },
                "Staff Assignments": {
                    "icon": "fas fa-user-tag", 
                    "groups": ["Admin", "Project Coordinator"],
                    "sub_items": {
                        "District Assignments": {
                            "icon": "fas fa-map-marker-alt", 
                            "url": "/personnel/district-assignments/", 
                            "groups": ["Admin", "Project Coordinator"]
                        },
                        "Region Assignments": {
                            "icon": "fas fa-globe", 
                            "url": "/personnel/region-assignments/", 
                            "groups": ["Admin", "Project Coordinator"]
                        },
                        "Sector Assignments": {
                            "icon": "fas fa-th", 
                            "url": "/personnel/sector-assignments/", 
                            "groups": ["Admin", "Project Coordinator"]
                        },
                    }
                },
                "Contractors": {
                    "icon": "fas fa-handshake", 
                    "url": "/personnel/contractors/", 
                    "groups": ["Admin", "Project Officer", "Project Coordinator"]
                },
            }
        },
        
        # "Geospatial Data": {
        #     "icon": "fas fa-map",
        #     "groups": ["Admin", "Project Officer", "Monitoring and Evaluation", "Regional Manager", "National"],
        #     "sub_items": {
        #         "Interactive Map": {
        #             "icon": "fas fa-map-marked-alt", 
        #             "url": "/map/", 
        #             "groups": ["Admin", "Project Officer", "Monitoring and Evaluation", "Regional Manager"]
        #         },
                
        #     }
        # },
        
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
                "ODK Data Integration": {
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
                "Certificate of Workdone": {
                    "icon": "fas fa-file-certificate", 
                    "groups": ["Admin", "Project Officer", "Monitoring and Evaluation"],
                    "sub_items": {
                        "CHED Certificates": {
                            "icon": "fas fa-file-alt", 
                            "url": "/certification/ched-certificates/", 
                            "groups": ["Admin", "Project Officer", "Monitoring and Evaluation"]
                        },
                        "HQ Receipts": {
                            "icon": "fas fa-receipt", 
                            "url": "/certification/hq-receipts/", 
                            "groups": ["Admin", "Project Officer", "Monitoring and Evaluation"]
                        },
                        "Sector Receipts": {
                            "icon": "fas fa-receipt", 
                            "url": "/certification/sector-receipts/", 
                            "groups": ["Admin", "Project Officer", "Monitoring and Evaluation"]
                        },
                    }
                },
                "Payment Management": {
                    "icon": "fas fa-money-check-alt", 
                    "groups": ["Admin", "Project Officer", "Regional Manager", "Project Manager"],
                    "sub_items": {
                        "Payment Reports": {
                            "icon": "fas fa-file-invoice", 
                            "url": "/payment/payment-reports/", 
                            "groups": ["Admin", "Project Officer", "Regional Manager"]
                        },
                        "Detailed Payment Reports": {
                            "icon": "fas fa-file-invoice-dollar", 
                            "url": "/payment/detailed-reports/", 
                            "groups": ["Admin", "Project Officer", "Regional Manager"]
                        },
                        "CalBank Momo Transactions": {
                            "icon": "fas fa-mobile-alt", 
                            "url": "/payment/calbank-transactions/", 
                            "groups": ["Admin", "Project Manager"]
                        },
                    }
                },
                "Equipment Management": {
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
                "Weekly Summary Reports": {
                    "icon": "fas fa-chart-line", 
                    "url": "/reports/weekly-summary/", 
                    "groups": ["Admin", "Monitoring and Evaluation", "Regional Manager"]
                },
                "Farm Database Reports": {
                    "icon": "fas fa-database", 
                    "url": "/reports/farm-database/", 
                    "groups": ["Admin", "Monitoring and Evaluation", "Regional Manager"]
                },
                "All Farm Queries": {
                    "icon": "fas fa-search", 
                    "url": "/reports/all-farm-queries/", 
                    "groups": ["Admin", "Monitoring and Evaluation", "Project Manager"]
                },
                "Special Projects": {
                    "icon": "fas fa-star", 
                    "url": "/reports/special-projects/", 
                    "groups": ["Admin", "Monitoring and Evaluation", "Project Manager"]
                },
                "Power BI Reports": {
                    "icon": "fas fa-chart-area", 
                    "url": "/reports/powerbi-reports/", 
                    "groups": ["Admin", "Monitoring and Evaluation", "Project Manager", "National"]
                },
            }
        },
        
        "System Administration": {
            "icon": "fas fa-cogs",
            "groups": ["Admin"],
            "sub_items": {
                "User Management": {
                    "icon": "fas fa-user-cog", 
                    "url": "/admin/auth/user/", 
                    "groups": ["Admin"]
                },
                "Group Management": {
                    "icon": "fas fa-users", 
                    "url": "/admin/auth/group/", 
                    "groups": ["Admin"]
                },
                "Sidebar Configuration": {
                    "icon": "fas fa-bars", 
                    "url": "/admin/system/sidebar/", 
                    "groups": ["Admin"]
                },
                "Background Tasks": {
                    "icon": "fas fa-tasks", 
                    "url": "/admin/system/background-tasks/", 
                    "groups": ["Admin"]
                },
                "System Version": {
                    "icon": "fas fa-code-branch", 
                    "url": "/admin/system/version/", 
                    "groups": ["Admin"]
                },
            }
        },
        
        "Feedback & Support": {
            "icon": "fas fa-comments",
            "url": "/feedback/",
            "groups": ["Admin", "Project Officer", "Monitoring and Evaluation", "District Officer", "Regional Manager"]
        },
        
        "Admin Panel": {
            "icon": "fas fa-user-shield",
            "url": "/admin/",
            "groups": ["Admin"]
        }
    }