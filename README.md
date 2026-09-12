# Interntion CRM

A complete, self-contained **Odoo 17** CRM built for **Interntion** — the UK
EduTech platform that places students into real, paid internships across
20+ industries (content modelled from [interntion.co.uk](https://interntion.co.uk/index.html)).

Everything required to run this project — the Odoo application, the
PostgreSQL database, the custom `interntion_crm` addon and the container
definitions — lives inside this **single folder** and is orchestrated with
Docker Compose. No manual Odoo/Postgres installation is required.

## What's inside

```
interntion-crm/
├── docker-compose.yml     # Odoo + Postgres + optional pgAdmin
├── Dockerfile             # Custom Odoo image with the Interntion addon baked in
├── odoo.conf               # Odoo server configuration
├── requirements.txt        # Extra Python deps for the addon
├── .env / .env.example     # Environment variables (db user/pass, ports)
└── addons/
    └── interntion_crm/      # The custom Odoo module
        ├── models/          # Employer, Internship, Mentor, Project, Service,
        │                    #   Testimonial, FAQ, Dashboard, CRM Lead extension
        ├── views/           # Forms, lists, kanban boards, menus
        ├── security/         # Access rights & groups
        └── data/             # Scraped seed data (services, employers, FAQ, ...)
```

## Features (mapped 1:1 from the Interntion website)

| Website feature | CRM implementation |
|---|---|
| "500+ Students Placed / 95% Success Rate / 50+ Industry Partners" | **Live Dashboard** (`Interntion CRM > Dashboard`) computed in real time from CRM data |
| Internship Opportunities (20+ sectors) | `Internship Opportunities` catalogue + dedicated **Applications Pipeline** (CRM pipeline: New Application → CV Screening → Matched with Employer → Interview → Offer Extended → Placed / Rejected) |
| Project Assistance (150+ AI/ML projects) | `Project Assistance` catalogue with category, level (BTech→PhD), tech stack |
| Work Experience Support (mentorship) | `Mentors` directory linked to each application |
| CV & Job Preparation | CV upload + "CV Reviewed" / "Mock Interview Done" / "Certificate Issued" tracking fields on every application |
| Industry Partners | `Industry Partners` (Employers) directory with sector, contact info, linked internships & applications |
| Student Stories / Testimonials | `Testimonials` records (Arjun Sharma, Priya Nair, Daniel Osei, etc.) |
| FAQ section | `FAQ` knowledge base (all 10 questions from the site) |
| "Apply Now" form (Name, Email, Phone, Course, CV upload) | New CRM Lead/Opportunity form (`x_course_stream`, `x_cv_file`, standard `partner_name`/`email_from`/`phone`) |

## Prerequisites

* [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine + Compose v2) installed and running.
* Ports `8069` (Odoo) and `5050` (pgAdmin, optional) free on your machine.

## Run it

Open a terminal in this folder (`interntion-crm/`) and run:

```powershell
docker compose up -d --build
```

Then open **http://localhost:8069** in your browser.

* On first launch Odoo shows the database manager. Create/select the database
  named in `odoo.conf` (`interntion_crm`) — the `interntion_crm` app will
  already be pre-loaded on the image, but if using a fresh database:
  1. Go to **Apps**, remove the "Apps" filter, search for **"Interntion CRM"**.
  2. Click **Install**.
* Login with the admin account you created, then open **Interntion CRM** from
  the main app menu.

To stop the stack:

```powershell
docker compose down
```

To stop and wipe all data (fresh start):

```powershell
docker compose down -v
```

### Optional: pgAdmin (inspect the database)

```powershell
docker compose --profile tools up -d
```

Then visit **http://localhost:5050** (login from `.env`), and add a server
pointing at host `db`, port `5432`, using the credentials from `.env`.

## Updating the module after code changes

The `addons/` folder is bind-mounted into the container, so edits to Python/XML
are picked up after an update:

```powershell
docker compose exec odoo odoo -u interntion_crm -d interntion_crm --stop-after-init
docker compose restart odoo
```

## Creating the Git repository

From this folder:

```powershell
git init
git add .
git commit -m "Initial commit: Interntion CRM (Odoo 17 + Docker)"
```

Then push to your remote of choice (GitHub, GitLab, Azure DevOps, etc.):

```powershell
git remote add origin <your-repo-url>
git branch -M main
git push -u origin main
```

> `.env` is git-ignored by default (it only holds local dev credentials — change
> `DB_PASSWORD` and `admin_passwd` in `odoo.conf` before any real deployment).

## Production hardening checklist

1. Change `admin_passwd` in `odoo.conf` and all DB credentials in `.env`.
2. Set `list_db = False` in `odoo.conf` once your database is created, to hide the database manager.
3. Put Odoo behind a reverse proxy (Nginx/Traefik) with HTTPS.
4. Enable regular `pg_dump` backups of the `interntion_db_data` volume.
5. Set `workers` in `odoo.conf` (e.g. `workers = 2`) for multi-process performance in production.
