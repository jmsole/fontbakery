# coding: utf-8
# Copyright 2013 The Font Bakery Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# See AUTHORS.txt for the list of Authors and LICENSE.txt for the License.
from bakery_lint.base import BakeryTestCase as TestCase, autofix
from bakery_cli.ttfont import Font
from bakery_cli.fixers import CharacterSymbolsFixer


class CheckNamesAreASCIIOnly(TestCase):

    name = __name__
    targets = ['result']
    tool = 'lint'

    @autofix('bakery_cli.fixers.CharacterSymbolsFixer')
    def test_check_names_are_ascii_only(self):
        """ NAME and CFF tables must not contain non-ascii characters """
        font = Font.get_ttfont(self.operator.path)

        for name in font.names:
            string = Font.bin2unistring(name)
            marks = CharacterSymbolsFixer.unicode_marks(string)
            if marks:
                self.fail('Contains {}'.format(marks))
