
class BuildError(Exception):
    pass

class DuplicateRuleError(Exception):
    def __init__(self, target):
        Exception.__init__(self, "Trying to add a duplicate rule: %s." % target)

class NoRuleError(Exception):
    def __init__(self, target):
        Exception.__init__(self, "No rule to build %s." % target)

class CyclicGraphError(Exception):
    def __init__(self, target, build_path):
        Exception.__init__(self, "Cyclic dependency detected for %s: %s." % (target, ', '.join(build_path)))

class NoSettingError(Exception):
    def __init__(self, setting):
        Exception.__init__(self, "No setting named %s." % setting)
