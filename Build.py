from datetime import datetime
from typing import List, Dict, Any, Tuple, Callable, Optional

from pymake.BaseRule import BaseRule
from pymake.builderrors import DuplicateRuleError, NoRuleError, CyclicGraphError, NoSettingError
from pymake.Settings import Settings

Rule = Any

class Build:
    def __init__(self):
        self.print_build = False
        self.rules = {}
        self.settings = Settings()
        self.trace = []
        self.build_tree = {}
        self.built_rules = set()

    def setSettingValue(self, name: str, value: Any) -> None:
        self.settings.setValue(name, value)

    def loadSettings(self, filename: str) -> None:
        self.settings.deserialise(filename)

    def saveSettings(self, filename: str) -> None:
        self.settings.serialise(filename)

    def createRule(self, name: str, rule_type = BaseRule) -> Rule:
        new_rule = rule_type(name)
        if name in self.rules:
            raise DuplicateRuleError(name)

        self.rules[name] = new_rule 
        return new_rule
    
    def computeBuildSubGraph(self, target: str, build_path: List[str] ) -> Tuple[bool, int]:
        if not target in self.rules:
            raise NoRuleError(target)
        if target in build_path:
            raise CyclicGraphError(target, build_path)

        if target in self.build_tree:
            if len(build_path) > 0 :
                self.build_tree[target]['dependants'].add(build_path[-1])
            needs_to_build = self.build_tree[target]['needs_to_build']
            last_build_time = self.build_tree[target]['last_build_time']
            return (needs_to_build, last_build_time)

        rule = self.rules[target]
        self.build_tree[target] = {}

        self.build_tree[target]['dependants'] = set()
        if len(build_path) > 0 :
            self.build_tree[target]['dependants'].add(build_path[-1])

        needs_to_build = rule.forceRebuild()
        self.build_tree[target]['needs_to_build'] = needs_to_build

        last_build_time = -1
        self.build_tree[target]['last_build_time'] = -1

        prerequisites = rule.getPrerequisites()
        self.build_tree[target]['prerequisites'] = set(prerequisites)

        if not rule.exists():
            needs_to_build = True
            self.build_tree[target]['needs_to_build'] = True
        else:
            last_build_time = rule.getLastBuildTime()
            self.build_tree[target]['last_build_time'] = last_build_time

        for setting in rule.getSettings():
            if not self.settings.exists(setting):
                raise NoSettingError(setting)
            elif last_build_time < self.settings.getLastBuildTime(setting):
                needs_to_build = True
                self.build_tree[target]['needs_to_build'] = True
                # Don't return from here as the whole dependency graph needs to be built up.
                break

        if len(prerequisites) == 0:
            return (needs_to_build, last_build_time)

        prerequisite_build_times: List[int] = []
        prerequisite_build_path = [*build_path, target]
        for dep in prerequisites:
            (dep_needs_to_build, dep_last_build_time) = self.computeBuildSubGraph(dep, prerequisite_build_path)
            if dep_needs_to_build or last_build_time < dep_last_build_time:
                needs_to_build = True
                self.build_tree[target]['needs_to_build'] = True
                # Don't break here as the loop has to run all the dependencies through the recurcive call.

        return (needs_to_build, last_build_time)

    def findNextBuildTargets(self):
        leaves = []
        for target, details in self.build_tree.items():
            if target in self.built_rules:
                continue
            elif not details['needs_to_build']:
                continue
            elif details['prerequisites'].issubset(self.built_rules):
                leaves.append( target)
        return leaves

    def build(self, target: str) -> None:

        self.build_tree = {}
        self.built_rules.clear()
        self.trace=[]

        self.computeBuildSubGraph(target, [])

        for target, details in self.build_tree.items():
            if target in self.built_rules:
                continue
            elif not details['needs_to_build']:
                self.built_rules.add(target)

        leaves = self.findNextBuildTargets()

        while len(leaves) > 0 :
            self.trace.append([])
            for leaf in leaves:
                try:
                    if self.print_build:
                        start_time = datetime.now()
                        print('Starting "%s" at %s' % (leaf, start_time))
                    settings_values = self.settings.getValuesForNames(self.rules[leaf].getSettings())
                    try:
                        self.rules[leaf].build(settings_values)
                        if self.print_build:
                            end_time = datetime.now()
                            print('    done "%s" at %s. Took %s' % (leaf, end_time, end_time - start_time))
                    except:
                        if self.print_build:
                            end_time = datetime.now()
                            print('    failed "%s" at %s. Took %s' % (leaf, end_time, end_time - start_time))
                        raise
                except:
                    raise

                self.built_rules.add(leaf)
                self.trace[-1].append(leaf)
            leaves = self.findNextBuildTargets()

    def drawGraph(self, file_name: str, rename_func: Optional[Callable[[str], str]] = None ) -> None:
        lines = []
        lines.append('digraph build_tree {')
        lines.append('graph [rankdir="LR"]')
        ids = {'_last_id': 1}

        def findOrInsert(name: str, ids: Dict[str,int]) -> int:
            if name in ids:
                return ids[name]
            last_id = ids['_last_id']
            last_id += 1
            ids[name] = last_id
            ids['_last_id'] = last_id
            return last_id

        for target, details in self.build_tree.items():
            tgt_id = findOrInsert(target, ids)
            if rename_func is not None:
                tgt_name = rename_func(target)

            lines.append('node_%s [label="%s"]' % (tgt_id, tgt_name))

            for dep in details['prerequisites']:
                dep_id = findOrInsert(dep, ids)
                lines.append('node_%s -> node_%s' % (dep_id, tgt_id))

        lines.append('}')

        with open(file_name, 'w') as fle:
            for line in lines:
                fle.write(line+'\n')

