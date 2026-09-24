"""Allowlisted saved Player fields; these are not verified live/boosted ratings."""

# Keep explicit schema names so unrelated enum fields ending in Rating are excluded.
RATING_FIELDS = tuple(name + 'Rating' for name in (
    'Speed', 'Acceleration', 'Agility', 'ChangeOfDirection', 'Strength',
    'Awareness', 'Jumping', 'Stamina', 'Toughness', 'Injury', 'Confidence',
    'ThrowPower', 'ThrowAccuracy', 'ThrowAccuracyShort', 'ThrowAccuracyMid',
    'ThrowAccuracyDeep', 'ThrowOnTheRun', 'ThrowUnderPressure', 'PlayAction', 'BreakSack',
    'Carrying', 'BCVision', 'BreakTackle', 'Trucking', 'StiffArm', 'SpinMove', 'JukeMove',
    'Catching', 'CatchInTraffic', 'SpectacularCatch', 'ShortRouteRunning',
    'MediumRouteRunning', 'DeepRouteRunning', 'Release',
    'PassBlock', 'PassBlockPower', 'PassBlockFinesse', 'RunBlock', 'RunBlockPower',
    'RunBlockFinesse', 'ImpactBlocking', 'LeadBlock',
    'Tackle', 'HitPower', 'Pursuit', 'PlayRecognition', 'BlockShedding',
    'PowerMoves', 'FinesseMoves', 'ManCoverage', 'ZoneCoverage', 'Press',
    'KickPower', 'KickAccuracy', 'KickReturn', 'LongSnap',
))


def read_ratings(data, info, fields, row, read_value):
    """Missing fields remain null; unsupported types/ranges fail instead of guessing."""
    values = {}
    for name in RATING_FIELDS:
        if name not in fields:
            values[name] = None
            continue
        field = fields[name]
        if field['type'] != 'int' or int(field.get('minValue', -1)) != 0 or int(field.get('maxValue', -1)) != 127:
            raise ValueError(f'Unsupported saved rating field: {name}')
        value = read_value(data, info, fields, row, name)
        if type(value) is not int or not 0 <= value <= 127:
            raise ValueError(f'Invalid saved rating: {name}')
        values[name] = value
    return values
