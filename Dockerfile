FROM odoo:19.0

USER root

# Extra Python dependencies used by the Interntion CRM module
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt --break-system-packages || \
    pip3 install --no-cache-dir -r /tmp/requirements.txt

# Custom addons are bind-mounted at runtime via docker-compose (./addons),
# this COPY guarantees the image is self-contained even without the bind mount.
COPY ./addons /mnt/extra-addons

USER odoo
