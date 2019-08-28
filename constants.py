"""
Collection of constants for modules
"""

# Admin id
# Add developer ID for passing the spam check and other commands
DEV = 255295801
# Add a ping channel
PING_CHANNEL = -353404420

# Duel constants
# Maximum STR the bot can roll
THRESHOLDCAP = 80
# Low and high accuracy that the user can get without exp
LOW_BASE_ACCURACY = 35
HIGH_BASE_ACCURACY = 50
# Exp multiplier for kills, deaths and misses
KILLMULT = 0.33
DEATHMULT = -0.12
MISSMULT = -0.05
# Always lose percent
ALWAYSLOSS = 0.05
HARDRESETCHANCE = 0.001  # 0.1%

# DO NOT TOUCH
# -----------------------------------------------------------
# Get the kill, death multiplier and their percentage to total
DATABASENAME = 'thedoomerbot.db'
KILLMULTPERC = round(KILLMULT / THRESHOLDCAP * 100, 2)
DEATHMULTPERC = round(DEATHMULT / THRESHOLDCAP * 100, 2)
MISSMULTPERC = round(MISSMULT / THRESHOLDCAP * 100, 2)
# Get the HARDCAP to additional strength
STRENGTHCAP = THRESHOLDCAP * (1 - ALWAYSLOSS)
ADDITIONALSTRCAP = STRENGTHCAP - LOW_BASE_ACCURACY
ADDITIONALPERCENTCAP = round(ADDITIONALSTRCAP / THRESHOLDCAP * 100, 2)
# Create dict with all duel data
DUELDICT = {
    'LOW_BASE_ACCURACY': LOW_BASE_ACCURACY,
    'HIGH_BASE_ACCURACY': HIGH_BASE_ACCURACY,
    'KILLMULT': KILLMULT,
    'DEATHMULT': DEATHMULT,
    'MISSMULT': MISSMULT,
    'STRENGTHCAP': STRENGTHCAP,
    'KILLMULTPERC': KILLMULTPERC,
    'DEATHMULTPERC': DEATHMULTPERC,
    'MISSMULTPERC': MISSMULTPERC,
    'ADDITIONALPERCENTCAP': ADDITIONALPERCENTCAP
}
# -----------------------------------------------------------

# Antispam constants
# Delays in seconds for the BOT
INDIVIDUAL_USER_DELAY = 10 * 60  # Ten minutes
INDIVIDUAL_REPLY_DELAY = 5 * 60  # Five minutes
ERROR_DELAY = 5 * 60  # One minute
# Duel cooldowns
CDREDUCTION = round(0.8 * INDIVIDUAL_USER_DELAY)  # 80%
SHORTCD = round(INDIVIDUAL_USER_DELAY - CDREDUCTION)

# Request timeout time in seconds
REQUEST_TIMEOUT = 3
