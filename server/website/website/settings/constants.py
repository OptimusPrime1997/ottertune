#
# OtterTune - constants.py
#
# Copyright (c) 2017-18, Carnegie Mellon University Database Group
#

# These parameters are not specified for any session, so they can only be set here

# If this flag is set, we check if celery is running, and restart celery if it is not.
# CHECK_CELERY = True
CHECK_CELERY = False

# address categorical knobs (enum, boolean)
ENABLE_DUMMY_ENCODER = False

# the threshold of check smooth
SMOOTH_THRESHOLD = 0.015

# continue count string
CONTINUE_COUNT = 'continue_count'
