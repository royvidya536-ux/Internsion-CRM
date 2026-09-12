{
    "name": "Interntion CRM",
    "version": "17.0.1.0.0",
    "category": "Sales/CRM",
    "summary": "Full CRM for Interntion - UK Paid Internship Placement Platform",
    "description": """
Interntion CRM
==============
A complete Odoo CRM built for Interntion, the UK EduTech platform that places
students into real, paid internships across 20+ industries.

Features
--------
* Internship Placement pipeline (CRM leads/opportunities) with dedicated stages:
  New Application -> CV Screening -> Matched with Employer -> Interview ->
  Offer Extended -> Placed / Rejected.
* Industry Partners (Employers) directory with sector, logo and partnership date.
* Internship Opportunities catalogue across 20+ sectors, paid/unpaid, stipend.
* Project Assistance catalogue (AI/ML/Data Science ready-to-submit projects).
* Mentors directory with expertise and assigned students.
* Our 4 core services showcase (Internship Opportunities, Project Assistance,
  Work Experience Support, CV & Job Preparation).
* Student testimonials / success stories.
* FAQ knowledge base.
* Interntion Dashboard with live KPIs: Students Placed, Success Rate,
  Industry Partners - matching the public website statistics, computed from
  real CRM data.
""",
    "author": "Interntion",
    "website": "https://interntion.co.uk",
    "license": "LGPL-3",
    "depends": ["base", "mail", "crm", "contacts", "board"],
    "data": [
        "security/interntion_security.xml",
        "security/ir.model.access.csv",
        "data/crm_stage_data.xml",
        "data/service_data.xml",
        "data/employer_data.xml",
        "data/mentor_data.xml",
        "data/internship_data.xml",
        "data/project_data.xml",
        "data/testimonial_data.xml",
        "data/faq_data.xml",
        "views/crm_lead_views.xml",
        "views/employer_views.xml",
        "views/internship_views.xml",
        "views/mentor_views.xml",
        "views/service_views.xml",
        "views/project_views.xml",
        "views/testimonial_views.xml",
        "views/faq_views.xml",
        "views/dashboard_views.xml",
        "views/menu_views.xml",
    ],
    "images": [],
    "installable": True,
    "application": True,
    "auto_install": False,
}
