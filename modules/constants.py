"""
Collection of constants for modules
"""

# Admin id
# Add developer ID for passing the spam check
DEVELOPER_ID = 255295801

# Duel constants
# Maximum STR the bot can roll
THRESHOLDCAP = 80
# Low and high accuracy that the user can get without exp
LOW_BASE_ACCURACY = 40
HIGH_BASE_ACCURACY = 60
# Exp multiplier for kills and deaths
KILLMULT = 0.16
DEATHMULT = 0.06
# Always lose percent
ALWAYSLOSS = 0.05
# Get the HARDCAP to additional strength
ADDITIONALHARDCAP = THRESHOLDCAP * (1 - ALWAYSLOSS) - LOW_BASE_ACCURACY

# Antispam constants
# Delays in seconds for the BOT
INDIVIDUAL_USER_DELAY = 10 * 60  # Ten minutes
INDIVIDUAL_REPLY_DELAY = 5 * 60  # Five minutes
ERROR_DELAY = 5 * 60  # One minute

# Request timeout time in seconds
REQUEST_TIMEOUT = 3
