from datetime import datetime
from typing import List, Dict, Any, Tuple, Callable, Optional, Union

from pymake.BaseRule import BaseRule
from pymake.builderrors import DuplicateRuleError, NoRuleError, CyclicGraphError, NoSettingError
from pymake.Settings import Settings

Rule = Any

class Build:
    def __init__(self):
        self.print_build = False
        self.colour_print_build = False
        self.rules = {}
        self.settings = Settings()
        self.trace = []
        self.build_tree = {}
        self.built_rules = set()
        self.dot_file_name = None
        self.dot_rename_func = None

    def _print(self, colour, *strings): 
        if not self.print_build:
            return 
        if not self.colour_print_build:
            print(*strings)
            return
        if colour == 'r':
            print('\033[91m', end='')
        elif colour == 'g':
            print('\033[92m', end='')
        elif colour == 'y':
            print('\033[93m', end='')
        elif colour == 'b':
            print('\033[94m', end='')
        print(*strings, end='')
        print('\033[0m')

    def setSettingValue(self, name: str, value: Any) -> None:
        self.settings.setValue(name, value)

    def loadSettings(self, filename: str) -> None:
        self.settings.deserialise(filename)

    def saveSettings(self, filename: str) -> None:
        self.settings.serialise(filename)

    def createRule(self, names: Union[str, List[str]], rule_type = BaseRule) -> Rule:
        if type(names) == str:
            names = [str(names)]

        new_rule = rule_type(names)
        for name in names:
            if name in self.rules:
                raise DuplicateRuleError(name)
            self.rules[name] = new_rule 

        return new_rule

    def setDotGraphOptions(self, file_name: str, rename_func: Optional[Callable[[str], str]] = None ) -> None:
        self.dot_file_name = file_name
        self.dot_rename_func = rename_func

    
    def _computeBuildSubGraph(self, target: str, build_path: List[str] ) -> Tuple[bool, int]:
        if not target in self.rules:
            raise NoRuleError(target)
        if target in build_path:
            raise CyclicGraphError(target, build_path)

        if target in self.build_tree:
            # if len(build_path) > 0 :
            #     self.build_tree[target]['dependants'].add(build_path[-1])
            needs_to_build = self.build_tree[target]['needs_to_build']
            last_build_time = self.build_tree[target]['last_build_time']
            return (needs_to_build, last_build_time)

        rule = self.rules[target]
        self.build_tree[target] = {}

        # self.build_tree[target]['dependants'] = set()
        # if len(build_path) > 0 :
        #     self.build_tree[target]['dependants'].add(build_path[-1])

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
            for tgt in rule.names:
                if tgt == target:
                    continue
                self.build_tree[tgt] = self.build_tree[target]
            return (needs_to_build, last_build_time)

        prerequisite_build_times: List[int] = []
        prerequisite_build_path = [*build_path, target]
        for dep in prerequisites:
            (dep_needs_to_build, dep_last_build_time) = self._computeBuildSubGraph(dep, prerequisite_build_path)
            if dep_needs_to_build or last_build_time < dep_last_build_time:
                needs_to_build = True
                self.build_tree[target]['needs_to_build'] = True
                # Don't break here as the loop has to run all the dependencies through the recurcive call.

        for tgt in rule.names:
            if tgt == target:
                continue
            self.build_tree[tgt] = self.build_tree[target]
        return (needs_to_build, last_build_time)

    def _findNextBuildTargets(self):
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

        self._print('b', 'Starting building dependency graph with %s rules.' % (len(self.rules.items())))

        self.build_tree = {}
        self.built_rules.clear()
        self.trace=[]

        start_time = datetime.now()
        self._computeBuildSubGraph(target, [])

        if self.dot_file_name is not None:
            self._drawGraph()

        targets_to_build = 0
        for target, details in self.build_tree.items():
            if target in self.built_rules:
                continue
            elif not details['needs_to_build']:
                self.built_rules.add(target)
            else:
                targets_to_build += 1

        leaves = self._findNextBuildTargets()

        end_time = datetime.now()
        self._print('g', '    Completed building dependency graph. Took %s' % (end_time-start_time))
        self._print('b', 'Found %s targets that need building.' % ( targets_to_build))

        total_start_time = datetime.now()

        while len(leaves) > 0 :
            self.trace.append([])
            for leaf in leaves:
                try:
                    if leaf in self.built_rules:
                        continue
                    rule = self.rules[leaf]
                    start_time = datetime.now()
                    self._print('b', 'Starting "%s" at %s' % (rule.getTargetStr(), start_time))
                    settings_values = self.settings.getValuesForNames(rule.getSettings())
                    try:
                        rule.build(settings_values)
                        end_time = datetime.now()
                        self._print('g', '    done "%s" at %s.\n     Took %s, Total %s' % (rule.getTargetStr(), end_time, end_time - start_time, end_time-total_start_time))
                    except:
                        end_time = datetime.now()
                        self._print('r', '    failed "%s" at %s.\n     Took %s, Total %s' % (rule.getTargetStr(), end_time, end_time - start_time, end_time-total_start_time))
                        raise
                except:
                    raise

                for name in rule.names:
                    self.built_rules.add(name)
                # self.trace[-1].append(leaf)
                self.trace[-1].extend(rule.names)
            leaves = self._findNextBuildTargets()

    def _drawGraph(self) -> None:
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
            if self.dot_rename_func is not None:
                tgt_name = self.dot_rename_func(target)
            else:
                tgt_name = target

            if tgt_name is not None:
                lines.append('node_%s [label="%s"]' % (tgt_id, tgt_name))

            for dep in details['prerequisites']:
                dep_id = findOrInsert(dep, ids)
                if dep_id is not None:
                    lines.append('node_%s -> node_%s' % (dep_id, tgt_id))

        lines.append('}')

        with open(self.dot_file_name, 'w') as fle:
            for line in lines:
                fle.write(line+'\n')


