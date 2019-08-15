"""
Collection of constants for modules
"""

# Admin id
# Add developer ID for passing the spam check
DEV = 255295801
# ID of the log chat
LOGCHATID = -398564859

# Duel constants
# Maximum STR the bot can roll
THRESHOLDCAP = 80
# Low and high accuracy that the user can get without exp
LOW_BASE_ACCURACY = 40
HIGH_BASE_ACCURACY = 60
# Exp multiplier for kills, deaths and misses
KILLMULT = 0.25
DEATHMULT = -0.12
MISSMULT = -0.05
# Always lose percent
ALWAYSLOSS = 0.05
HARDRESETCHANCE = 0.001 # 0.1%

# DO NOT TOUCH
# -----------------------------------------------------------
# Get the kill, death multiplier and their percentage to total
KILLMULTPERC = round(KILLMULT / THRESHOLDCAP * 100, 2)
DEATHMULTPERC = round(DEATHMULT / THRESHOLDCAP * 100, 2)
MISSMULTPERC = round(MISSMULT / THRESHOLDCAP * 100, 2)
# Get the HARDCAP to additional strength
STRENGTHCAP = THRESHOLDCAP * (1 - ALWAYSLOSS)
ADDITIONALSTRCAP = STRENGTHCAP - LOW_BASE_ACCURACY
ADDITIONALPERCENTCAP = round(ADDITIONALSTRCAP / THRESHOLDCAP * 100, 2)
# -----------------------------------------------------------

# Antispam constants
# Delays in seconds for the BOT
INDIVIDUAL_USER_DELAY = 10 * 60  # Ten minutes
INDIVIDUAL_REPLY_DELAY = 5 * 60  # Five minutes
ERROR_DELAY = 5 * 60  # One minute

# Request timeout time in seconds
REQUEST_TIMEOUT = 3
