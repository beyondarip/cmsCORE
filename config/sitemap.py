from django.contrib.sitemaps import Sitemap
from django.urls import reverse

class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'daily'

    def items(self):
        return ['home', 'profile', 'news', 'mitra', 'management', 'ukm', 'manajemen', 'fisika_medis','statistika', 'informatika','exchange','manajemens2', 'akuntansi', 'hospar', 'dkv', 'arsitektur', 'k3','pedoman_akademik','kalender_akademik']

    def location(self, item):
        return reverse(item) 