# Copyright 2014 Mike Wakerly <opensource@hoho.com>
#
# This file is part of the Pykeg package of the Kegbot project.
# For more information on Pykeg or Kegbot, see http://kegbot.org/
#
# Pykeg is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# Pykeg is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pykeg.  If not, see <http://www.gnu.org/licenses/>.

import random

from django.contrib import messages
from django.db import transaction
from django.db.models import Count
from django.shortcuts import redirect
from django.utils.safestring import SafeString
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from pykeg.core import backend
from pykeg.core import models
from pykeg.contrib.demomode.util import random_item

MIN_KEG_VOLUME_ML = 800
RANDOM_POUR_RANGE_ML = (100, 500)

@csrf_exempt
@never_cache
@require_http_methods(["POST"])
@transaction.atomic
def summon_drinker(request):
    user = random_item(models.User)
    tap = random_item(models.KegTap)
    beer_type = random_item(models.BeerType)

    if not tap or not user or not beer_type:
        messages.error(request, 'No drinkers are available!')
        return redirect('kb-home')

    be = backend.KegbotBackend()

    # End keg if it's near empty.
    if tap.current_keg and tap.current_keg.remaining_volume() < MIN_KEG_VOLUME_ML:
        be.end_keg(tap)

    # Start keg if the tap is idle.
    if not tap.current_keg:
        be.start_keg(tap, beer_type=beer_type)

    volume_ml = random.randint(*RANDOM_POUR_RANGE_ML)
    drink = be.record_drink(tap.meter_name, ticks=0, volume_ml=volume_ml,
        username=user.username)

    message = 'We poked <strong>%s</strong>, who just poured <a href="%s">Drink %s</a>.' % (
        user.username, drink.get_absolute_url(), drink.id)
    messages.success(request, SafeString(message))

    return redirect('kb-home')

