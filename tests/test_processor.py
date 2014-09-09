# -*- coding: utf-8 -*-

import logging, pprint, unittest
from usep_gh_handler_app.utils.processor import XIncludeUpdater


log = logging.getLogger(__name__)


class XIncludeUpdaterTest( unittest.TestCase ):
    """ Tests Parser functions.
            To use:
            - activate the virtual environment
            - cd to tests directory
            - run `python ./test_processor.py` or `python ./test_processor.py XIncludeUpdaterTest._make_filename` """

    # def test_make_filename(self):
    #     updater = XIncludeUpdater( log=log )
    #     segment = u'/path/to/file/CA.Berk.UC.HMA.L.8-4286.xml'
    #     self.assertEqual(
    #         u'CA.Berk.UC.HMA.L.8-4286.xml',
    #         updater._make_filename( segment )
    #         )

    # end class XIncludeUpdaterTest()




if __name__ == "__main__":
    unittest.TestCase.maxDiff = None    # allows error to show in long output
    unittest.main()
