## **1. Project Overview**

**Goal**  
Build a university website CMS system enabling non-technical staff to manage content across multiple page types. The system should offer:

- Flexible, template-based page creation
- Comprehensive SEO and performance considerations
- Role-based access control
- High security and maintainability

**Technology Stack**  
- **Backend**: Django (Python)
- **Frontend**: Tailwind CSS + JavaScript
- **Database**: Relational DB (e.g., PostgreSQL or MySQL) or any Django-supported engine
- **Hosting**: Containerized or conventional (depends on the institution’s infrastructure)

---

## **2. Core Requirements**

### **2.1 Content Management**

1. **Dynamic Content Editing**
   - All text, images, and media on each page can be edited through the CMS.
   - Rich text editor support (e.g., WYSIWYG).
   - Media upload (images, videos, documents) with version tracking.

2. **Page Types Required**
   - **Homepage**
   - **Program/Department pages**
   - **Faculty profiles**
   - **News/Articles**
   - **Scholarship information**
   - **Partnership pages**
   - **About/Profile pages**
   - **Student admission pages**

3. **Specific Content Blocks**  
   (Routes/Sections/pages) 
   - **Home**
     - Banner
     - Kenapa Matana? (Reasons)
     - Berita & Acara (News)
   - **Profil**
     - Profil Matana (Visi Misi, Sejarah, Keunggulan, Fasilitas)
     - Manajemen (Rektorat & Ketua Lembaga, Dekan & Ketua Program Studi)
     - Mitra (Hospital, Hotel, Institusi & Perusahaan, Universitas, Bank)
   - **Program Studi** (TBD info)
   - **Pendaftaran (Admission)**
     - Alur Pendaftaran
     - Daftar Sekarang
     - Biaya Kuliah
     - E-Book (Panduan PMB)
   - **Beasiswa (Scholarship)**
   - **Kemahasiswaan**
     - UKM
     - Student Exchange
     - Alumni (TBD)
   - **Media**
     - Matana News
     - Matana Event
     - Matana Podcast
     - Matana TV

4. **SEO & Performance**
   - Each page has custom meta tags (title, description, keywords).
   - Performance optimization techniques (minification, caching).
   - Security best practices applied throughout (e.g., input sanitization).

---

### **2.2 User Management**

- **Role-Based Access Control (RBAC)**
  - **Super Admin**: Full system control, can manage user roles.
  - **Admin**: Permissions to edit specific content and upload media.

- **Granular Permissions**
  - Ability to grant “edit” or “view-only” access for specific pages/apps.

- **Audit Logging**
  - Track changes to content blocks (who edited, date/time, versioning).

---

## **3. Technical Architecture**

### **3.1 Minimalistic File Structure**

To keep the project organized yet reduce the total number of files, we propose the following **lean** Django project layout. This layout combines settings into a single file, uses environment variables for sensitive data, and groups each core feature into its own Django app.

```
cms/
├── manage.py
├── requirements.txt         # Single requirements file
├── .env                     # Environment variables (excluded from VCS)
│
├── config/          # Main project folder
│   ├── __init__.py
│   ├── settings.py          # Single settings file (use .env for secrets)
│   ├── urls.py              # Root URL configurations
│   ├── wsgi.py
│   └── asgi.py              # Only if ASGI is needed
│
├── apps/                    # All Django apps in one folder
│   ├── core/                # Core functionalities, common models
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── views.py
│   │   └── urls.py
│   ├── pages/               # Dynamic page mgmt, content blocks
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── views.py
│   │   └── urls.py
│   ├── media/               # File handling, validations, possibly versioning
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── models.py
│   │   ├── views.py
│   │   └── urls.py
│   └── users/               # User mgmt & role-based access control
│       ├── __init__.py
│       ├── admin.py
│       ├── apps.py
│       ├── models.py
│       ├── views.py
│       └── urls.py
│
├── templates/               # HTML templates
│   └── pages/               # Page-specific templates
│       └── ...
└── static/                  # Static files (CSS, JS, Images)
    ├── css/
    ├── js/
    └── img/
```

**Key Points:**

- **Single Settings File**: `settings.py` uses environment variables from `.env` for sensitive or environment-specific settings (e.g., `SECRET_KEY`, DB credentials).
- **apps**: Each folder is a Django “app” dedicated to a specific domain.
- **templates** and **static**: All templating and static assets grouped in a straightforward manner.
- **requirements.txt**: Holds all package dependencies (for both dev and production).

---

### **3.2 Data Model Design Pattern**

Instead of multiple models for each page type, we use a **flexible, JSON-based** design. Below are references to example structures (not for direct implementation but to illustrate the concept).

```plaintext
# Example structure - not for direct implementation
class ContentBlock:
    identifier = CharField()         # e.g., 'homepage_banner', 'about_vision'
    content_type = CharField()       # e.g., 'text', 'rich_text', 'image'
    content = JSONField()            # store actual content data
    page = ForeignKey(Page)
```

```plaintext
# Example structure - not for direct implementation
class Page:
    template = CharField()           # references a template file (e.g., 'homepage.html')
    slug = SlugField()
    metadata = JSONField()           # SEO metadata, page settings
    status = CharField()             # 'draft' or 'published'
```

**How it fits together:**

- **`Page`**: Stores high-level info about the page (template reference, slug, SEO data).
- **`ContentBlock`**: Holds each chunk of content or media, tied to a `Page`.  
  This approach allows you to easily add, remove, or rearrange content blocks as needed without altering the entire database schema.

---

### **3.3 Key Technical Decisions**

1. **Content Storage & Versioning**
   - Use Django’s built-in JSON field for flexible content storage.
   - Implement content versioning so editors can revert if needed.
   - Leverage caching for frequently accessed content (e.g., homepage).

2. **Media Management**
   - File validation and potentially auto-resizing for images to ensure performance.
   - Organized media library with folder-based structure and usage tracking.

3. **Security Considerations**
   - **Input Sanitization**: Protect against XSS, injection attacks.
   - **CSRF Protection**: Leverage Django’s CSRF middleware.
   - **Role-Based Access Control**: Granular permissions for editing and publishing.
   - **Content Approval Workflow**: Optionally add approval states if multiple roles are involved.

---

## **4. Admin Interface Requirements**

1. **Content Editor (WYSIWYG)**
   - Rich text editing (bold, italic, links, images).
   - **Live Preview**: Editors should see how the final content looks.
   - **Version History**: Track versions for each content block.
   - **Draft vs. Published** states to handle multi-step approval.

2. **Media Library**
   - Drag-and-drop file uploads.
   - Simple folder/album organization.
   - Track where each file is used (pages referencing it).

3. **User Management**
   - Create/edit/delete roles.
   - Assign specific permissions (e.g., can publish news, can only edit scholarships).
   - Audit log: who changed what, and when.

---

## **5. API Structure (Example References)**

Below is a **sample API structure** for a headless or partially headless implementation. This is **not** actual production code—just an illustration.

```plaintext
# Example endpoints - not for direct implementation

api/
  ├── pages/
  │   ├── GET /api/pages/           # List pages
  │   ├── POST /api/pages/          # Create page
  │   └── PATCH /api/pages/{id}/    # Update page
  ├── content/
  │   ├── GET /api/content/{id}/    # Get content block
  │   └── PUT /api/content/{id}/    # Update content
  └── media/
      ├── POST /api/media/          # Upload media
      └── GET /api/media/           # List media
```

**Usage Context:**

- **GET /api/pages/**: Retrieves a list of pages with their slugs and statuses for display in the admin.
- **POST /api/pages/**: Creates a new page record; might also generate default content blocks.
- **PUT /api/content/{id}/**: Updates a specific content block with new text or media references.

---

## **6. Implementation Guidelines**

### **6.1 Database Considerations**

- Use migrations (Django’s `makemigrations`, `migrate`) for schema changes.
- Add indexes on frequently queried fields (e.g., `slug`).
- Use caching (e.g., Redis) for frequently accessed pages.

### **6.2 Testing Requirements**

- **Unit Tests**: Validate individual functions or classes (e.g., content versioning).
- **Integration Tests**: Confirm that user role permissions, content workflows, and media uploads work cohesively.
- **Performance Tests**: Ensure pages load under 3 seconds (standard benchmark).
- **Security Tests**: Check user role restrictions, XSS & CSRF protections.

### **6.3 Performance Requirements**

- Page load times **< 3s**.
- Optimized for concurrency (multiple editors working at once).
- Efficient file delivery (CDN or caching for static/media files).

### **6.4 Deployment Requirements**

- Support multiple environments (local, staging, production).
- Backup & restore strategies (database dumps, media backups).
- Logging & monitoring for error tracking.
- Optional CI/CD pipeline for automated testing and deployment.

---

## **7. Future Considerations**

1. **Content Scheduling**: Schedule content to go live/publish at a future time.
2. **Advanced Analytics**: Deeper usage tracking, A/B testing, or user engagement metrics.

---

## **8. Success Metrics**

- **Content Editor Satisfaction**: Low friction for everyday tasks, minimal bugs.
- **Page Load Performance**: Pages consistently meeting the <3s target.
- **System Uptime**: High availability, minimal downtime.
- **Content Update Frequency**: Editors can safely update content without developer assistance.
- **User Engagement**: Time on page, bounce rates, conversion (e.g., admissions sign-ups).

---

## **9. References & Context**

1. **Minimal File Structure**  
   - Ensures an easily maintainable codebase with consolidated `settings.py` and environment variables in `.env`.
2. **Example Code & Responses**  
   - The PRD includes references to pseudo-code for data models (`ContentBlock`, `Page`), an example file structure, and sample API endpoints. These are **not** for direct usage but guide how the system might be architected in Django.





Media Library/Uploader/media management digunakan untuk mengupload media ke server dan mengelola media yang sudah diupload.
dan juga bisa juga digunakan oleh user untuk memilih media yang ingin digunakan untuk content, dan juga bisa mengupload media sendiri.
media ini bersifat public, artinya media ini bisa diakses oleh semua user.
