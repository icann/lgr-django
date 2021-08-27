from django.test import override_settings

from lgr_advanced.lgr_editor.forms import MetadataForm
from lgr_models.tests.test_unicode_version import TestUnicodeVersion


class TestMetaDataUnicodeVersion(TestUnicodeVersion):

    def test_unicode_versions(self):
        """
        Verify the list displayed is unfiltered and contains all supported versions
        """
        self.a_unicode_version.activated = True
        self.a_unicode_version.save()
        metadata_form = MetadataForm(additional_repertoires=[], disabled=False)
        self.assertSetEqual(set(metadata_form.fields['unicode_version'].choices),
                            {(v, v) for v in self.versions_supported})
