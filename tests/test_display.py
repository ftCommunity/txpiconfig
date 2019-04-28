# -*- coding: utf-8 -*-
#
# Config -- An application to configure a TX-Pi.
#
# Written in 2019 by Lars Heuer
#
# To the extent possible under law, the author(s) have dedicated all copyright
# and related and neighboring rights to this software to the public domain
# worldwide. This software is distributed without any warranty.
# You should have received a copy of the CC0 Public Domain Dedication along
# with this software.
#
# If not, see <http://creativecommons.org/publicdomain/zero/1.0/>.
#
"""Some tests regarding display config parsing.
"""
import pytest
from config import _parse_display_config


@pytest.mark.parametrize('s,expected', [('dtoverlay=waveshare35b-v2:rotate=180\n', ('waveshare35b-v2', 180, None, None)),
                                        ('dtoverlay=waveshare35b-v2\n', ('waveshare35b-v2', None, None, None)),
                                        ('dtoverlay=waveshare35a:rotate=180\n', ('waveshare35a', 180, None, None)),
                                        ('dtoverlay=waveshare35a:rotate=180,speed=40000000\n', ('waveshare35a', 180, 40000000, None)),
                                        ('dtoverlay=waveshare35a:rotate=180,speed=40000000,fps=50\n', ('waveshare35a', 180, 40000000, 50)),
                                        ('dtoverlay=waveshare35a:speed=40000000,fps=50\n', ('waveshare35a', None, 40000000, 50)),
                                        ('dtoverlay=waveshare35a:speed=40000000\n', ('waveshare35a', None, 40000000, None)),
                                        ('dtoverlay=waveshare35a:speed=40000000,rotate=90\n', ('waveshare35a', 90, 40000000, None)),
                                        ('dtoverlay=waveshare35a:fps=24,speed=27000000,rotate=90\n', ('waveshare35a', 90, 27000000, 24)),
                                        ])
def test_parse_displayconfig(s, expected):
    res = _parse_display_config(s)
    assert res
    assert expected == tuple(res)


if __name__ == '__main__':
    pytest.main([__file__])
