from django.contrib.auth.models import User
from django.test import TestCase

from .constants import position, status, region_status
from .models import Language, Page, Region
from .forms.language_tree import LanguageTreeNodeForm
from .forms.languages import LanguageForm
from .forms.pages import PageForm
from .forms.regions import RegionForm


# pylint: disable=too-many-instance-attributes
class SetupClass(TestCase):
    @staticmethod
    def create_region(region_data):
        region_form = RegionForm(region_data)
        region_form.is_valid()
        region_form.save()
        return Region.objects.get(slug=region_data['name'])

    @staticmethod
    def create_language(language_data):
        language_form = LanguageForm(language_data)
        language_form.is_valid()
        language_form.save()
        return Language.objects.get(name=language_data['name'])

    @staticmethod
    def create_language_tree_node(language_tree_node_data, region_slug=None):
        language_tree_node_form = LanguageTreeNodeForm(data=language_tree_node_data,
                                                       region_slug=region_slug)
        language_tree_node_form.is_valid()
        return language_tree_node_form.save_language_node()

    @staticmethod
    # pylint: disable=too-many-arguments
    def create_page(page_data, user, region_slug, language_code,
                    page_id=None, publish=False, archived=False):
        # TODO: fix form usage to page_form and page_translation_form
        page_form = PageForm(
            page_data,
            page_id=page_id,
            publish=publish,
            archived=archived,
            region_slug=region_slug,
            language_code=language_code,
            user=user
        )
        if page_form.is_valid():
            return page_form.save()
        return None

    def setUp(self):
        self.user = User.objects.create_user('test', 'test@integreat.com', 'test')
        self.region = self.create_region({
            'name': 'demo',
            'events_enabled': True,
            'push_notifications_enabled': True,
            'push_notification_channels': 'channel1 channel2',
            'latitude': 10.0,
            'longitude': 20.0,
            'postal_code': '10000',
            'admin_mail': 'admin@integreat.com',
            'statistics_enabled': False,
            'matomo_url': '',
            'matomo_token': '',
            'matomo_ssl_verify': True,
            'status': region_status.ACTIVE,
        })

        self.english = self.create_language({
            'name': 'English',
            'code': 'en-us',
            'text_direction': 'ltr'
        })

        self.deutsch = self.create_language({
            'name': 'Deutsch',
            'code': 'de-de',
            'text_direction': 'ltr'
        })

        self.arabic = self.create_language({
            'name': 'Arabic',
            'code': 'ar-ma',
            'text_direction': 'rtl'
        })

        self.english_node = self.create_language_tree_node(
            language_tree_node_data={
                'language': self.english.id,
                'parent': None,
                'active': True
            }, region_slug='demo'
        )

        self.deutsch_node = self.create_language_tree_node(
            language_tree_node_data={
                'language': self.deutsch.id,
                'parent': self.english_node.id,
                'active': True,
            }, region_slug='demo')

        self.arabic_node = self.create_language_tree_node(
            language_tree_node_data={
                'language': self.arabic.id,
                'parent': self.english_node.id,
                'active': True
            }, region_slug='demo')

        self.page_tunews = self.create_page(
            page_data={
                'title': 'big news',
                'text': '''
                    <p>First Layer</p>
                    <div style="width: 100%;background: #0079ad;text-align: center">
                        hello world
                        <a href="http://tunewsinternational.com/">international test</a>
                        2019-04-05 11:53:44
                    </div>
                ''',
                'status': status.PUBLIC,
                'position': position.FIRST_CHILD,
                'parent': None,
                'icon': None,
                'public': True
            },
            user=self.user,
            region_slug='demo',
            language_code='en-us',
            publish=True
        )

        self.page_slot_one = self.create_page(
            page_data={
                'title': 'Slot1',
                'text': '''
                <p>Slot 1</p>
                <div style="width: 100%;background: #0079ad;text-align: center">
                    E-news No: 12345 - 
                    <a href="http://tunewsinternational.com/">TüNews INTERNATIONAL</a> 
                    - 2019-04-05 11:53:44
                </div>''',
                'status': status.PUBLIC,
                'position': position.FIRST_CHILD,
                'parent': self.page_tunews.id,
                'icon': None,
                'public': True
            },
            user=self.user,
            region_slug='demo',
            language_code='en-us',
            publish=True
        )

        self.create_page(
            page_data={
                'title': 'Schlitz1',
                'text': 'zweite Schicht Schlitz eins',
                'status': status.PUBLIC,
                'position': position.FIRST_CHILD,
                'parent': self.page_tunews.id,
                'icon': None,
                'public': True
            },
            user=self.user,
            page_id=self.page_slot_one.id,
            region_slug='demo',
            language_code='de-de',
            publish=True
        )

        self.page_slot_two = self.create_page(
            page_data={
                'title': 'Slot2',
                'text': 'second layer slot two',
                'status': status.PUBLIC,
                'position': position.LAST_CHILD,
                'parent': self.page_tunews.id,
                'icon': None,
                'public': True
            },
            user=self.user,
            region_slug='demo',
            language_code='en-us',
            publish=True
        )

        self.page_tunews_two = self.create_page(
            page_data={
                'title': 'Tunews two',
                'text': 'first layer',
                'status': status.PUBLIC,
                'position': position.FIRST_CHILD,
                'parent': None,
                'icon': None,
                'public': True
            },
            user=self.user,
            region_slug='demo',
            language_code='en-us',
            publish=True
        )


class LanguageTreeNodeTestCase(SetupClass):
    def test_node_region(self):
        self.assertEqual(self.english_node.region, self.region)

    def test_parent_node(self):
        self.assertEqual(self.deutsch_node.parent, self.english_node)


class PageFormTestCase(SetupClass):
    def test_page(self):
        self.assertEqual(len(self.page_tunews.languages), 1)
        self.assertEqual(len(self.page_slot_one.languages), 2)
        self.assertEqual(len(self.page_slot_two.languages), 1)

        self.assertIsNone(self.page_tunews.get_translation('de-de'))
        self.assertIsNotNone(self.page_slot_one.get_translation('de-de'))

    def test_pages(self):
        pages = Page.get_tree(region_slug=self.region.slug)
        self.assertEqual(len(pages), 4)
