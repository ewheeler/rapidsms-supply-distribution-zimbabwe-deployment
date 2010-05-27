#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8


from django.templatetags.tabs_tags import register_tab

from rapidsms.utils.render_to_response import render_to_response
#from rapidsms.utils.pagination import paginated

from .models import Shipment

@register_tab(caption="Shipments")
def index(req):
    template_name="logistics/index.html"
    context = {}
    #context['entries'] = paginated(req, all, per_page=50)
    context['shipments'] = Shipment.objects.all()
    return render_to_response(req, template_name, context )
