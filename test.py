import os
import sys
import unittest
from time import sleep

if __name__ == "__main__":
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..')))

from pymake import Build
from pymake.filerules import FileTouchRule
from pymake.builderrors import DuplicateRuleError, NoRuleError, CyclicGraphError

def removeIfExists(path: str) -> None:
    if os.path.exists(path):
        os.remove(path)

def touchFile(path: str) -> None:
    fle = open(path,'a')
    fle.close()
    sleep(1e-3)

class BuildSingeTestCase(unittest.TestCase):
    def tearDown(self):
        removeIfExists("a.txt")

    def test_DNE(self):
        build = Build()
        build.createRule('a.txt', FileTouchRule)

        build.build('a.txt')
        self.assertListEqual(build.trace, [['a.txt']])

    def test_exists(self):
        touchFile('a.txt')

        build = Build()
        build.createRule('a.txt', FileTouchRule)

        build.build('a.txt')
        self.assertListEqual(build.trace, [])

    def test_NoRuleError(self):

        build = Build()

        with self.assertRaises(NoRuleError):
            build.build('a.txt')

    def test_DuplicateRuleError(self):

        build = Build()
        build.createRule('a.txt', FileTouchRule)

        with self.assertRaises(DuplicateRuleError):
            build.createRule('a.txt', FileTouchRule)

class BuildTwoTestCase(unittest.TestCase):
    def tearDown(self):
        removeIfExists("a.txt")
        removeIfExists("b.txt")

    def test_IndependentTargets_DNE(self):
        build = Build()
        build.createRule('a.txt', FileTouchRule)
        build.createRule('b.txt', FileTouchRule)

        build.build('a.txt')
        self.assertListEqual(build.trace, [['a.txt']])

        build.build('b.txt')
        self.assertListEqual(build.trace, [['b.txt']])

    def test_IndependentTargets_OneExists(self):
        touchFile('a.txt')

        build = Build()
        build.createRule('a.txt', FileTouchRule)
        build.createRule('b.txt', FileTouchRule)

        build.build('a.txt')
        self.assertListEqual(build.trace, [])

        build.build('b.txt')
        self.assertListEqual(build.trace, [['b.txt']])

    def test_DependentTargets_DNE(self):
        build = Build()
        a = build.createRule('a.txt', FileTouchRule)
        a.addPrerequisite('b.txt')

        build.createRule('b.txt', FileTouchRule)

        build.build('a.txt')
        self.assertListEqual(build.trace, [['b.txt'],['a.txt']])

    def test_DependentTargets_TopDNE(self):
        touchFile('b.txt')

        build = Build()
        a = build.createRule('a.txt', FileTouchRule)
        a.addPrerequisite('b.txt')

        build.createRule('b.txt', FileTouchRule)

        build.build('a.txt')
        self.assertListEqual(build.trace, [['a.txt']])

    def test_DependentTargets_BottomDNE(self):
        touchFile('a.txt')

        build = Build()
        a = build.createRule('a.txt', FileTouchRule)
        a.addPrerequisite('b.txt')

        build.createRule('b.txt', FileTouchRule)

        build.build('a.txt')
        self.assertListEqual(build.trace, [['b.txt'], ['a.txt']])

    def test_DependentTargets_BottomNewer(self):
        touchFile('a.txt')
        touchFile('b.txt')

        build = Build()
        a = build.createRule('a.txt', FileTouchRule)
        a.addPrerequisite('b.txt')

        build.createRule('b.txt', FileTouchRule)

        build.build('a.txt')
        self.assertListEqual(build.trace, [['a.txt']])

    def test_DependentTargets_BottomForceRebuild(self):
        touchFile('b.txt')
        touchFile('a.txt')

        build = Build()
        a = build.createRule('a.txt', FileTouchRule)
        a.addPrerequisite('b.txt')

        b = build.createRule('b.txt', FileTouchRule)
        b.setForceRebuild(True)


        build.build('a.txt')
        self.assertListEqual(build.trace, [['b.txt'], ['a.txt']])

    def test_MissingPrerequisite(self):
        build = Build()
        a = build.createRule('a.txt', FileTouchRule)
        a.addPrerequisite('b.txt')

        with self.assertRaises(NoRuleError):
            build.build('a.txt')

class BuildThreeTestCase(unittest.TestCase):
    def tearDown(self):
        removeIfExists("a.txt")
        removeIfExists("b.txt")
        removeIfExists("c.txt")

    def test_Tree_DNE(self):
        build = Build()
        a = build.createRule('a.txt', FileTouchRule)
        a.addPrerequisite('b.txt')
        a.addPrerequisite('c.txt')

        build.createRule('b.txt', FileTouchRule)
        build.createRule('c.txt', FileTouchRule)

        build.build('a.txt')
        self.assertListEqual(build.trace, [['b.txt', 'c.txt'],['a.txt']])

    def test_Tree_SubTreeDNE(self):
        touchFile('b.txt')

        build = Build()
        a = build.createRule('a.txt', FileTouchRule)
        a.addPrerequisite('b.txt')
        a.addPrerequisite('c.txt')

        build.createRule('b.txt', FileTouchRule)
        build.createRule('c.txt', FileTouchRule)

        build.build('a.txt')
        self.assertListEqual(build.trace, [['c.txt'],['a.txt']])

    def test_Tree_TopNewer(self):
        touchFile('c.txt')
        touchFile('b.txt')
        touchFile('a.txt')

        build = Build()
        a = build.createRule('a.txt', FileTouchRule)
        a.addPrerequisite('b.txt')
        a.addPrerequisite('c.txt')

        build.createRule('b.txt', FileTouchRule)
        build.createRule('c.txt', FileTouchRule)

        build.build('a.txt')
        self.assertListEqual(build.trace, [])

    def test_Tree_SubTreeNewer(self):
        touchFile('c.txt')
        touchFile('a.txt')
        touchFile('b.txt')

        build = Build()
        a = build.createRule('a.txt', FileTouchRule)
        a.addPrerequisite('b.txt')
        a.addPrerequisite('c.txt')

        build.createRule('b.txt', FileTouchRule)
        build.createRule('c.txt', FileTouchRule)

        build.build('a.txt')
        self.assertListEqual(build.trace, [['a.txt']])

    def test_Tree_NoRebuilds(self):

        build = Build()
        a = build.createRule('a.txt', FileTouchRule)
        a.addPrerequisite('b.txt')
        a.addPrerequisite('c.txt')

        b = build.createRule('b.txt', FileTouchRule)
        b.addPrerequisite('c.txt')

        build.createRule('c.txt', FileTouchRule)

        build.build('a.txt')
        self.assertListEqual(build.trace, [['c.txt'], ['b.txt'], ['a.txt']])

    def test_Line_DNE(self):

        build = Build()
        a = build.createRule('a.txt', FileTouchRule)
        a.addPrerequisite('b.txt')

        b = build.createRule('b.txt', FileTouchRule)
        b.addPrerequisite('c.txt')

        build.createRule('c.txt', FileTouchRule)

        build.build('a.txt')
        self.assertListEqual(build.trace, [['c.txt'], ['b.txt'], ['a.txt']])

    def test_Line_BottomDNE(self):
        touchFile('b.txt')
        touchFile('a.txt')

        build = Build()
        a = build.createRule('a.txt', FileTouchRule)
        a.addPrerequisite('b.txt')

        b = build.createRule('b.txt', FileTouchRule)
        b.addPrerequisite('c.txt')

        build.createRule('c.txt', FileTouchRule)

        build.build('a.txt')
        self.assertListEqual(build.trace, [['c.txt'], ['b.txt'], ['a.txt']])

    def test_Line_BottomNewer(self):
        touchFile('b.txt')
        touchFile('a.txt')
        touchFile('c.txt')

        build = Build()
        a = build.createRule('a.txt', FileTouchRule)
        a.addPrerequisite('b.txt')

        b = build.createRule('b.txt', FileTouchRule)
        b.addPrerequisite('c.txt')

        build.createRule('c.txt', FileTouchRule)

        build.build('a.txt')
        self.assertListEqual(build.trace, [['b.txt'], ['a.txt']])

    def test_CyclicGraphError(self):

        build = Build()
        a = build.createRule('a.txt', FileTouchRule)
        a.addPrerequisite('b.txt')

        b = build.createRule('b.txt', FileTouchRule)
        b.addPrerequisite('c.txt')

        c = build.createRule('c.txt', FileTouchRule)
        c.addPrerequisite('a.txt')

        with self.assertRaises(CyclicGraphError):
            build.build('a.txt')

class SeetingsTestCase(unittest.TestCase):
    def tearDown(self):
        removeIfExists("a.txt")
        removeIfExists("b.txt")

    def test_SettingsOlder(self):
        build = Build()

        build.setSettingValue('b', 'b')
        build.setSettingValue('a', 'a')
        touchFile('b.txt')
        touchFile('a.txt')

        a = build.createRule('a.txt', FileTouchRule)
        a.addPrerequisite('b.txt')
        a.addSetting('a')

        b = build.createRule('b.txt', FileTouchRule)
        b.addSetting('b')

        build.build('a.txt')
        self.assertListEqual(build.trace, [])

    def test_SettingsOlderReorder(self):
        build = Build()

        build.setSettingValue('a', 'a')
        build.setSettingValue('b', 'b')
        touchFile('b.txt')
        touchFile('a.txt')

        a = build.createRule('a.txt', FileTouchRule)
        a.addPrerequisite('b.txt')
        a.addSetting('a')

        b = build.createRule('b.txt', FileTouchRule)
        b.addSetting('b')

        build.build('a.txt')
        self.assertListEqual(build.trace, [])

    def test_BottomSettingNewer(self):
        build = Build()

        build.setSettingValue('a', 'a')
        touchFile('b.txt')
        touchFile('a.txt')
        build.setSettingValue('b', 'b')

        a = build.createRule('a.txt', FileTouchRule)
        a.addPrerequisite('b.txt')
        a.addSetting('a')

        b = build.createRule('b.txt', FileTouchRule)
        b.addSetting('b')

        build.build('a.txt')
        self.assertListEqual(build.trace, [['b.txt'], ['a.txt']])

    def test_TopSettingNewer(self):
        build = Build()

        build.setSettingValue('b', 'b')
        touchFile('b.txt')
        touchFile('a.txt')
        build.setSettingValue('a', 'a')

        a = build.createRule('a.txt', FileTouchRule)
        a.addPrerequisite('b.txt')
        a.addSetting('a')

        b = build.createRule('b.txt', FileTouchRule)
        b.addSetting('b')

        build.build('a.txt')
        self.assertListEqual(build.trace, [['a.txt']])

    def test_TopSettingReset(self):
        build = Build()

        build.setSettingValue('a', 'a')
        build.setSettingValue('b', 'b')
        touchFile('b.txt')
        touchFile('a.txt')
        build.setSettingValue('a', 'changed')

        a = build.createRule('a.txt', FileTouchRule)
        a.addPrerequisite('b.txt')
        a.addSetting('a')

        b = build.createRule('b.txt', FileTouchRule)
        b.addSetting('b')

        build.build('a.txt')
        self.assertListEqual(build.trace, [['a.txt']])

    def test_TopSettingResetUnchanged(self):
        build = Build()

        build.setSettingValue('a', 'a')
        build.setSettingValue('b', 'b')
        touchFile('b.txt')
        touchFile('a.txt')
        build.setSettingValue('a', 'a')

        a = build.createRule('a.txt', FileTouchRule)
        a.addPrerequisite('b.txt')
        a.addSetting('a')

        b = build.createRule('b.txt', FileTouchRule)
        b.addSetting('b')

        build.build('a.txt')
        self.assertListEqual(build.trace, [])


if __name__ == "__main__":
    unittest.main()

