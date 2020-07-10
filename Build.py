from typing import List, Dict, Any, Tuple
from pymake import BaseRule
from pymake.builderrors import DuplicateRuleError, NoRuleError, CyclicGraphError

Rule = Any

class Build:

    def __init__(self):

        self.print_build = False
        self.rules = {}
        self.trace = []
        self.build_tree = {}
        self.built_rules = set()


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

        if len(prerequisites) == 0:
            return (needs_to_build, last_build_time)

        prerequisite_build_times: List[int] = []
        prerequisite_build_path = [*build_path, target]
        for dep in prerequisites:
            (dep_needs_to_build, dep_last_build_time) = self.computeBuildSubGraph(dep, prerequisite_build_path)
            if dep_needs_to_build:
                needs_to_build = True
            else:
                prerequisite_build_times.append( dep_last_build_time)

        if needs_to_build:
            self.build_tree[target]['needs_to_build'] = True
        else:
            max_prerequisite_build_time = max(prerequisite_build_times)
            if last_build_time < max_prerequisite_build_time:
                needs_to_build = True
                self.build_tree[target]['needs_to_build'] = True
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
                        print('Starting %s' % leaf)
                    self.rules[leaf].build()
                    if self.print_build:
                        print('  done')
                except:
                    raise

                self.built_rules.add(leaf)
                self.trace[-1].append(leaf)
            leaves = self.findNextBuildTargets()

