from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.pages.models import Article, ArticleCategory, ProgramStudi, ProdiAdmin
from django.utils.text import slugify
from django.contrib.auth import get_user_model
import random
from datetime import timedelta
import time
from django.contrib.auth.models import Group

User = get_user_model()

class Command(BaseCommand):
    help = 'Generates sample academic articles with relevant content'

    def add_arguments(self, parser):
        parser.add_argument('count', type=int, help='Number of articles to generate')

    
    def create_prodi_admin_group(self):
        # Create admin group
        prodi_group, created = Group.objects.get_or_create(name='prodi_admin')
        
        # Create default Program Studi entries
        default_prodi = [
            {
                'nama': 'Artikel',
                'slug': 'article',
                'description': 'Program Studi Artikel'
            },
            {
                'nama': 'Desain Komunikasi Visual',
                'slug': 'dkv',
                'description': 'Program Studi Desain Komunikasi Visual'
            },
            {
                'nama': 'Akutansi', 
                'slug': 'akutansi',
                'description': 'Program Studi Akutansi'
            },
            {
                'nama': 'Arsitektur',
                'slug': 'arsitektur',
                'description': 'Program Studi Arsitektur'
            },
            {
                'nama': 'Hospitality',
                'slug': 'hospitality',
                'description': 'Program Studi Hospitality'
            },
            {
                'nama': 'Magister Manajemen',
                'slug': 'magister_manajemen',   
                'description': 'Program Studi Magister Manajemen'
            },
            {
                'nama': 'K3',
                'slug': 'k3',
                'description': 'Program Studi K3'
            },
            {
                'nama': 'Fisika Medis',
                'slug': 'fisika_medis',
                'description': 'Program Studi Fisika Medis'
            },
            {
                'nama': 'Statistika',
                'slug': 'statistika',
                'description': 'Program Studi Statistika'
            },
            {
                'nama': 'Informatika',
                'slug': 'informatika',
                'description': 'Program Studi Informatika'
            },
            {
                'nama': 'Media',
                'slug': 'media',
                'description': 'Program Studi Media'
            },
            {
                'nama': 'Admin',
                'slug': 'admin',
                'description': 'Program Studi Admin'
            },
            {
                'nama': 'Manajemen',
                'slug': 'manajemen',
                'description': 'Program Studi Manajemen'
            }
        ]
        
        # First, create all Program Studi
        created_prodis = {}
        for prodi_data in default_prodi:
            prodi, created = ProgramStudi.objects.get_or_create(
                slug=prodi_data['slug'],
                defaults={
                    'name': prodi_data['nama'],
                    'description': prodi_data['description']
                }
            )
            created_prodis[prodi_data['slug']] = prodi

        # Get the media prodi for default access
        media_prodi = created_prodis['media']
        article_prodi = created_prodis['article']
        admin_prodi = created_prodis['admin']
        
        # Now create users and assign them to their prodi plus media access
        for prodi_data in default_prodi:
            if prodi_data['slug'] == 'media':  # Skip creating separate admin for article/media
                continue
            if prodi_data['slug'] == 'article':  # Skip creating separate admin for article/media
                continue
            if prodi_data['slug'] == 'admin':  # Skip creating separate admin for article/media
                continue
                    

            prodi = created_prodis[prodi_data['slug']]
            username = f"admin_{prodi_data['slug']}"
            email = f"{username}@matanauniversity.ac.id"
            password = "Matana2024!"  # Default password
            
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=prodi_data['nama'],
                    is_staff=True
                )
                user.groups.add(prodi_group)
                
                # Create ProdiAdmin entry
                prodi_admin, created = ProdiAdmin.objects.get_or_create(
                    user=user,
                    defaults={'is_active': True}
                )
                # Add both their own prodi and media prodi
                prodi_admin.program_studi.add(prodi)
                prodi_admin.program_studi.add(media_prodi)
                prodi_admin.program_studi.add(article_prodi)
                
                print(f"Created admin user for {prodi_data['nama']}")
                print(f"Username: {username}")
                print(f"Password: {password}")
                print(f"Access to: {prodi_data['nama']} and Media")
                print("---")

    def handle(self, *args, **kwargs):
        count = kwargs['count']
        self.create_prodi_admin_group()
        
        # return
        # Get admin user
        try:
            admin_user = User.objects.get(username='admin')
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Admin user not found. Please create a user with username "admin" first.')
            )
            return
        
        # Buat atau dapatkan kategori
        categories_data = ['Akademik', 'Beasiswa', 'Prestasi', 'Event', 'Penelitian']
        categories = []
        for cat_name in categories_data:
            category, created = ArticleCategory.objects.get_or_create(
                name=cat_name,
                defaults={
                    'slug': slugify(cat_name),
                    'description': f'Kategori untuk artikel {cat_name.lower()}'
                }
            )
            categories.append(category)
        
        academic_titles = [
            "Matana University Menjalin Kerjasama dengan Industri Teknologi Terkemuka",
            "Program Beasiswa Unggulan Matana University 2024",
            "Prestasi Mahasiswa Matana di Kompetisi Nasional",
            "Seminar Internasional: Teknologi dan Bisnis di Era Digital",
            "Workshop Kewirausahaan: Dari Kampus Menuju Startup",
            "Matana University Membuka Program Studi Baru",
            "Kunjungan Industri: Mahasiswa Matana di Silicon Valley",
            "Penelitian Terbaru: Inovasi Teknologi Kampus",
            "Career Fair 2024: Peluang Karir Lulusan Matana",
            "Kuliah Umum: Transformasi Digital dalam Pendidikan",
        ]

        excerpts = [
            "Pengembangan kerjasama strategis untuk meningkatkan kualitas pendidikan dan peluang karir mahasiswa.",
            "Program beasiswa unggulan untuk mahasiswa berprestasi dengan berbagai fasilitas pendukung.",
            "Mahasiswa Matana meraih prestasi gemilang dalam kompetisi tingkat nasional.",
            "Menghadirkan pembicara internasional dalam seminar teknologi dan bisnis.",
            "Pelatihan intensif kewirausahaan untuk mahasiswa dengan mentor berpengalaman.",
            "Pembukaan program studi baru yang sesuai dengan kebutuhan industri.",
            "Program kunjungan industri ke perusahaan teknologi global.",
            "Hasil penelitian terbaru dalam pengembangan teknologi kampus.",
            "Membuka peluang karir dengan perusahaan mitra terkemuka.",
            "Kuliah umum dengan topik terkini tentang transformasi digital.",
        ]

        content_template = """
        {excerpt}

        Program ini merupakan bagian dari komitmen Matana University dalam:
        
        1. Meningkatkan kualitas pendidikan
        2. Mengembangkan kompetensi mahasiswa
        3. Memperkuat kerjasama dengan industri
        4. Mendukung inovasi dan penelitian
        
        Untuk informasi lebih lanjut, mahasiswa dapat menghubungi:
        - Email: info@matanauniversity.ac.id
        - Telepon: (021) XXX-XXXX
        - Website: www.matanauniversity.ac.id
        """
        
        for i in range(count):
            title = random.choice(academic_titles)
            excerpt = random.choice(excerpts)
            timestamp = int(time.time())
            created_date = timezone.now() - timedelta(days=random.randint(0, 30))
            
            # Create unique slug by adding timestamp
            unique_slug = f"{slugify(title)}-{timestamp}"
            
            try:
                article = Article.objects.create(
                    title=title,
                    slug=unique_slug,
                    excerpt=excerpt,
                    content=content_template.format(excerpt=excerpt),
                    status='published',
                    category=random.choice(categories),
                    created_at=created_date,
                    updated_at=created_date,
                    published_at=created_date,
                    created_by=admin_user,
                    updated_by=admin_user,
                    featured_image='/static/images/article2.jpg'
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created article: "{title}"')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Failed to create article: "{title}". Error: {str(e)}')
                )
            
            # Tambahkan jeda kecil untuk memastikan timestamp berbeda
            time.sleep(0.1)
